import {Component, Input, OnInit} from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";
import {ApiResponse, ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {CommonService} from "../../services/common/common.service";
import {error} from "util";
import {TestBedService} from "./test-bed.service";
import {UserService} from "../../services/user/user.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";

enum EditMode {
  NONE = 0,
  MANUAL_LOCK_INITIAL = "Set manual lock",
  MANUAL_LOCK_UPDATE_EXPIRATION = "Update manual lock expiration",
  MANUAL_LOCK_ADD_TIME = "Add time to manual lock"
}

@Component({
  selector: 'app-test-bed',
  templateUrl: './test-bed.component.html',
  styleUrls: ['./test-bed.component.css']
})
export class TestBedComponent implements OnInit {
  @Input() embed: boolean = false;
  schedulingTime = {hour: 1, minute: 1};
  addedTime: number;
  testBeds: any [] = null;
  automationStatus = {};
  manualStatus = {};
  assetLevelManualLockStatus = {};
  currentEditMode: EditMode = EditMode.NONE;
  currentTestBed: any = null;
  EditMode = EditMode;
  users: any = null;
  lockPanelHeader: string = null;
  selectedUser: any = null;
  assetSelectedUser: any = null;
  assets = null;
  driver = null;
  refreshing: string = null;
  userMap: any = null;
  tempDescription: string;
  tempNote: string;



  constructor(private regressionService: RegressionService,
              private apiService: ApiService,
              private loggerService: LoggerService,
              private commonService: CommonService,
              private service: TestBedService,
              private userService: UserService,
              private modalService: NgbModal
  ) { }

  ngOnInit() {
    // fetchUsers
    // fetchTestbeds
    this.driver = new Observable(observer => {
      observer.next(true);
      //observer.complete();
      return () => {
      };
    }).pipe(
      switchMap(response => {
        return this.fetchTestBeds();
      }),
      switchMap(response => {
        return this.fetchAutomationStatus();
      }),
      switchMap(response => {
        return this.getUsers();
      }),
      switchMap(response => {
        return this.userService.getUserMap();
      }),
      switchMap(response => {
        this.userMap = response;
        return this.fetchAssets();
      })
      );
    this.refreshAll();
  }

  refreshAll () {
    this.refreshing = "Refreshing test-beds";
    this.driver.subscribe(() => {
      this.refreshing = null;
    }, error => {
      this.loggerService.error("Unable to init test-bed component");
    });
  }

  refreshTestBeds() {
    this.fetchTestBeds().subscribe();
  }

  fetchAssets() {
    if (!this.embed) {
      return this.service.assets().pipe(switchMap(response => {
        let dutAssets = [];
        let hostAssets = [];
        let perfListenerAssets = [];
        this.assets = response;
        this.assets.map((asset) => {
          asset.applyingManualLock = false;
          asset.selectedUser = null;
          if (asset.type === 'DUT') {
            dutAssets.push(asset);
          }
          if (asset.type === 'Host') {
            hostAssets.push(asset);
          }
          if (asset.type === 'Perf Listener') {
            perfListenerAssets.push(asset);
          }
        });
        this.assets = [...dutAssets, ...hostAssets, ...perfListenerAssets];
        return of(true);
      }))
    } else {
      return of(true);
    }

  }

  fetchTestBeds() {
    return this.regressionService.fetchTestbeds().pipe(switchMap(response => {
      this.testBeds = response;
      this.testBeds.map(testBed => {
        testBed.editingDescription = false;
        testBed.editingNote = false;
        let numExecutions = -1;
        let executionId = -1;
        this.automationStatus[testBed.name] = {numExecutions: numExecutions,
          executionId: executionId};

        this.manualStatus[testBed.name] = {manualLock: testBed.manual_lock,
        manualLockExpiryTime: testBed.manual_lock_expiry_time,
        manualLockSubmitter: testBed.manual_lock_submitter};
        this.assetLevelManualLockStatus[testBed.name] = null;
        if (testBed.hasOwnProperty("asset_level_manual_lock_status")) {
          this.assetLevelManualLockStatus[testBed.name] = testBed.asset_level_manual_lock_status;
        }
      });
      this.automationStatus = {...this.automationStatus};

      return of(this.testBeds);
    }))
  }

  fetchAutomationStatus() {
    return forkJoin(...this.testBeds.map((testBed) => {
      return this.regressionService.testBedInProgress(testBed.name).pipe(switchMap(response => {
        let numExecutions = -1;
        let executionId = -1;
        let manualLock = false;
        if (testBed.name === 'fs-42') {
          let i = 0;
        }
        this.automationStatus[testBed.name] = {numExecutions: numExecutions,
          executionId: executionId,
          manualLock: manualLock};
          if (response && response.hasOwnProperty("automation_status")) {
            /*
            let numExecutions = response.length;
            let executionId = numExecutions;
            if (numExecutions > 0) {
              let thisResponse = response[0];
              executionId = thisResponse.execution_id;
            }*/
            let automationStatus = response.automation_status;
            if (automationStatus.hasOwnProperty("internal_asset_in_use") && automationStatus.internal_asset_in_use) {
              this.automationStatus[testBed.name] = {numExecutions: 1,
                executionId: automationStatus.internal_asset_in_use_suite_id, assetInUse: automationStatus.internal_asset};
            } else if (automationStatus.hasOwnProperty("used_by_suite_id")) {
              this.automationStatus[testBed.name] = {numExecutions: 1, executionId: automationStatus.used_by_suite_id};
            } else if (automationStatus.hasOwnProperty('suite_info') && automationStatus.suite_info) {
              this.automationStatus[testBed.name] = {numExecutions: 1, executionId: automationStatus.suite_info.suite_execution_id};
            }

          }
        return of(null);
        }))
      })
    )
  }

  setLockPanelHeader(string) {
    this.lockPanelHeader = `${this.currentEditMode} ${string}`;
  }

  onLock(content, testBed) {
    this.currentEditMode = this.EditMode.MANUAL_LOCK_INITIAL;
    this.setLockPanelHeader(`for ${testBed.name}`);
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title', size: 'lg', backdrop: 'static'});


  }

  onUnLock(testBed) {
    if (confirm(`Are you sure, you want to unlock ${testBed.name}`)) {
      let url = "/api/v1/regression/test_beds/" + this.currentTestBed.id;
      let payload = {manual_lock: false};
      this.apiService.put(url, payload).subscribe(response => {
        this.loggerService.success(`Unlock submitted for ${testBed.name}`);
        //window.location.reload();
        this.refreshTestBeds();
      }, error => {
        this.loggerService.error(`Unlock ${testBed.name} failed`);
      })

    }
  }

  onExtendTime(content, testBed) {
    this.currentEditMode = this.EditMode.MANUAL_LOCK_UPDATE_EXPIRATION;
    this.setLockPanelHeader(`for ${testBed.name}`);
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title', backdrop: 'static'});


  }

  onAddTime(content, testBed) {
    this.currentEditMode = this.EditMode.MANUAL_LOCK_ADD_TIME;
    this.setLockPanelHeader(`for ${testBed.name}`);
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title', backdrop: 'static'});
  }

  onAddTimeSubmit(testbed) {
    let url = "/api/v1/regression/test_beds/" + this.currentTestBed.id;
    let payload = {manual_lock_extension_hour: this.addedTime, manual_lock_extension_minute: 0};
    this.apiService.put(url, payload).subscribe(response => {
      this.loggerService.success("Time successfully added");
      this.refreshTestBeds();
      this.currentEditMode = EditMode.NONE;
    }, error => {
      this.loggerService.error("Unable to add time");
    });
    testbed['addClick'] = false;
  }

  onExtendTimeSubmit(testBed) {
    let url = "/api/v1/regression/test_beds/" + this.currentTestBed.id;
    let payload = {manual_lock_extension_hour: this.schedulingTime.hour,
    manual_lock_extension_minute: this.schedulingTime.minute};
    this.apiService.put(url, payload).subscribe(response => {
      this.loggerService.success("Extension request submitted");
      this.refreshTestBeds();
      this.currentEditMode = EditMode.NONE;
    }, error => {
      this.loggerService.error("Unable to extend lock");
    });
    testBed['extendClick'] = false;
  }


  onLockSubmit() {
    if (!this.selectedUser) {
      return this.loggerService.error("Please select a user");
    }
    console.log(this.selectedUser);
    console.log(this.schedulingTime.hour);
    console.log(this.schedulingTime.minute);
    let url = "/api/v1/regression/test_beds/" + this.currentTestBed.id;
    let payload = {manual_lock_submitter_email: this.selectedUser.email,
    manual_lock: true, manual_lock_extension_hour: this.schedulingTime.hour,
    manual_lock_extension_minute: this.schedulingTime.minute};
    this.apiService.put(url, payload).subscribe(response => {
      this.loggerService.success("Lock request submitted");
      this.selectedUser = null;
      this.schedulingTime.hour = 1;
      this.schedulingTime.minute = 1;
      this.refreshTestBeds();
      //window.location.reload();
      this.currentEditMode = EditMode.NONE;
    }, error => {
      if (error.value instanceof ApiResponse) {
        this.loggerService.error("Unable to submit lock: " + error.value.error_message);
      } else {
        this.loggerService.error("Unable to submit lock");
      }

    })
  }


  onCancelLockPanel(testBed) {
    this.currentEditMode = this.EditMode.NONE;
    testBed['extendClick'] = false;
    testBed['addClick'] = false;
  }

  getUsers() {
    return this.apiService.get("/api/v1/users").pipe(switchMap(response => {
      this.users = response.data;
      return of(null);
    }));
  }

  getPrettyTime(t) {
    return this.commonService.getPrettyLocalizeTime(t);
  }

  isLockExpired(testBed) {
    let expired = false;
    if (this.manualStatus[testBed.name].manualLock) {
      let expiryTime = this.commonService.convertToLocalTimezone(this.manualStatus[testBed.name].manualLockExpiryTime);
      if (expiryTime < new Date()) {
        expired = true;
      }
    }
    return expired;
  }

  lockAsset(asset) {
    if (!asset.selectedUser) {
      return this.loggerService.error('Please select a user');
    }
    let name = asset.name;
    this.service.lockAsset(name, asset.type, asset.selectedUser).subscribe((response) => {
      this.loggerService.success(`Asset ${name} lock submitted`);
      asset.applyingManualLock = false;
      asset.selectedUser = null;
      this.refreshAll();
    }, error => {
      this.loggerService.error(`Unable to lock asset: ${name}`);
    })
  }

  unlockAsset(asset) {
    let name = asset.name;
    this.service.unlockAsset(name, asset.type).subscribe((response) => {
      this.loggerService.success(`Asset: ${name} unlock submitted`);
      asset.applyingManualLock = false;
      this.refreshAll();

    }, error => {
      this.loggerService.error(`Unable to unlock asset: ${name}`);
    })
  }

  onSubmitDescription(testBed) {
    let payload = {description: testBed.description};
    this.apiService.put('/api/v1/regression/test_beds/' + testBed.id, payload).subscribe((response) => {
      this.loggerService.success('Successfully updated!');
    }, error => {
      this.loggerService.error("Unable to update description");
    });
    testBed.editingDescription = false;
  }

  onEditDescription(testBed) {
    this.tempDescription = testBed.description;
    testBed.editingDescription = true;
  }

  onEditNote(testBed) {
    this.tempNote = testBed.note;
    testBed.editingNote = true;

  }

  onSubmitNote(testBed) {
    let payload = {note: testBed.note};
    this.apiService.put('/api/v1/regression/test_beds/' + testBed.id, payload).subscribe((response) => {
      this.loggerService.success('Successfully updated!');
    }, error => {
      this.loggerService.error("Unable to update note");
    });
    testBed.editingNote = false;
    this.tempNote = "";

  }

  onCancelNote(testBed) {
    testBed.note = this.tempNote;
    testBed.editingNote = false;

  }

  onCancelDescription(testBed) {
    testBed.description = this.tempDescription;
    testBed.editingDescription = false;
  }
}
