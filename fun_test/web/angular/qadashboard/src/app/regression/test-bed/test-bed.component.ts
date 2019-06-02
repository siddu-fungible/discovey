import {Component, Input, OnInit} from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";
import {ApiResponse, ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {CommonService} from "../../services/common/common.service";
import {error} from "util";

enum EditMode {
  NONE = 0,
  MANUAL_LOCK_INITIAL = "Set manual lock",
  MANUAL_LOCK_UPDATE_EXPIRATION = "Update manual lock expiration"
}

@Component({
  selector: 'app-test-bed',
  templateUrl: './test-bed.component.html',
  styleUrls: ['./test-bed.component.css']
})
export class TestBedComponent implements OnInit {
  @Input() embed: boolean = false;
  schedulingTime = {hour: 1, minute: 1};
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

  constructor(private regressionService: RegressionService, private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService
  ) { }

  ngOnInit() {
    // fetchUsers
    // fetchTestbeds
    let o = new Observable(observer => {
      observer.next(true);
      observer.complete();
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
      }));

    o.subscribe(() => {

    }, error => {
      this.loggerService.error("Unable to init test-bed component");
    })
  }

  refreshTestBeds() {
    this.fetchTestBeds().subscribe();
  }

  fetchTestBeds() {
    return this.regressionService.fetchTestbeds().pipe(switchMap(response => {
      this.testBeds = response;
      this.testBeds.map(testBed => {
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

  onLock(testBed) {
    this.currentEditMode = this.EditMode.MANUAL_LOCK_INITIAL;
    this.setLockPanelHeader(`for ${testBed.name}`);
  }

  onUnLock(testBed) {
    if (confirm(`Are you sure, you want to unlock ${testBed.name}`)) {
      let url = "/api/v1/regression/test_beds/" + this.currentTestBed.id;
      let payload = {manual_lock: false};
      this.apiService.put(url, payload).subscribe(response => {
        this.loggerService.success(`Unlock submitted for ${testBed.name}`);
        window.location.reload();
        //this.refreshTestBeds();
      }, error => {
        this.loggerService.error(`Unlock ${testBed.name} failed`);
      })

    }
  }

  onExtendTime(testBed) {
    this.currentEditMode = this.EditMode.MANUAL_LOCK_UPDATE_EXPIRATION;
    this.setLockPanelHeader(`for ${testBed.name}`);

  }

  onExtendTimeSubmit() {
    let url = "/api/v1/regression/test_beds/" + this.currentTestBed.id;
    let payload = {manual_lock_extension_hour: this.schedulingTime.hour,
    manual_lock_extension_minute: this.schedulingTime.minute};
    this.apiService.put(url, payload).subscribe(response => {
      this.loggerService.success("Extension request submitted");
      this.refreshTestBeds();
      this.currentEditMode = EditMode.NONE;
    }, error => {
      this.loggerService.error("Unable to extend lock");
    })
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
      //this.refreshTestBeds();
      window.location.reload();
      this.currentEditMode = EditMode.NONE;
    }, error => {
      if (error.value instanceof ApiResponse) {
        this.loggerService.error("Unable to submit lock: " + error.value.error_message);
      } else {
        this.loggerService.error("Unable to submit lock");
      }

    })
  }

  onCloseLockPanel() {
    this.currentEditMode = this.EditMode.NONE;
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
}
