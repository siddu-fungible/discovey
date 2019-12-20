import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {RegressionService} from "../regression/regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";
import {ApiResponse, ApiService} from "../services/api/api.service";
import {CommonService} from "../services/common/common.service";
import {TestBedService} from "../regression/test-bed/test-bed.service";
import {UserService} from "../services/user/user.service";
import {LoggerService} from "../services/logger/logger.service";

enum EditMode {
  NONE = 0,
  MANUAL_LOCK_INITIAL = "Set manual lock",
  MANUAL_LOCK_UPDATE_EXPIRATION = "Update manual lock expiration"
}

class FlatNode {
  name: string = null;
  leaf: boolean = false;
  hide: boolean = true;
  indent: number = 0;
  children: FlatNode[] = [];
}

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css'],
})

export class TestComponent implements OnInit {

  @Input() data: any = null;
  @Output() clickedNode: EventEmitter<any> = new EventEmitter();
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
  assetSelectedUser: any = null;
  assets = null;
  driver = null;
  refreshing: string = null;
  userMap: any = null;
  editingDescription: boolean = false;
  currentDescription: string;
  flatNodes: FlatNode[] = [];

  constructor(private regressionService: RegressionService,
              private apiService: ApiService,
              private loggerService: LoggerService,
              private commonService: CommonService,
              private service: TestBedService,
              private userService: UserService
  ) {
  }

  ngOnInit() {
    if (this.data) {
      for (let d of this.data) {
        let flatNode = new FlatNode();
        flatNode.name = d["name"];
        flatNode.leaf = d["leaf"];
        flatNode.children = [];
        flatNode.indent = 0;
        flatNode.hide = false;
        this.flatNodes.push(flatNode);
        this.setFlatNodes(d, flatNode, 0);
      }
    }

    // fetchUsers
    // fetchTestbeds
    // this.driver = new Observable(observer => {
    //   observer.next(true);
    //   //observer.complete();
    //   return () => {
    //   };
    // }).pipe(
    //   switchMap(response => {
    //     return this.fetchTestBeds();
    //   }),
    //   switchMap(response => {
    //     return this.fetchAutomationStatus();
    //   }),
    //   switchMap(response => {
    //     return this.getUsers();
    //   }),
    //   switchMap(response => {
    //     return this.userService.getUserMap();
    //   }),
    //   switchMap(response => {
    //     this.userMap = response;
    //     return this.fetchAssets();
    //   })
    //   );
    // this.refreshAll();
  }

  setFlatNodes(d, node, indent): FlatNode {
    if (!d["leaf"]) {
      for (let child of d["children"]) {
        let flatNode = new FlatNode();
        flatNode.name = child["name"];
        flatNode.leaf = child["leaf"];
        flatNode.children = [];
        flatNode.indent = indent + 1;
        this.flatNodes.push(flatNode);
        let childFlatNode = this.setFlatNodes(child, flatNode, indent + 1);
        node.children.push(childFlatNode);
      }
    }
    return node;
  }

  clickNode(flatNode) {
    if (!flatNode.leaf) {
      for (let child of flatNode.children) {
        if (child.hide) {
          this.expandNode(child);
        } else {
          this.collapseNode(child);
        }
      }
    } else {
      this.clickedNode.emit(flatNode);
    }
  }

  expandNode(node): void {
    node.hide = false;
  }

  collapseNode(node): void {
    if (!node.leaf) {
      for (let child of node.children) {
        this.collapseNode(child);
      }
    }
    node.hide = true;
  }

  getIndentHtml = (node) => {
    let s = "";
    if (node.hasOwnProperty("indent")) {
      for (let i = 0; i < node.indent - 1; i++) {
        s += "<span style=\"color: white\">&rarr;</span>";
      }
      if (node.indent)
        s += "<span>&nbsp;&nbsp;</span>";
    }

    return s;
  };


  refreshAll() {
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

        testBed['editing_mode'] = false;
        console.log(testBed);
        let numExecutions = -1;
        let executionId = -1;

        this.automationStatus[testBed.name] = {
          numExecutions: numExecutions,
          executionId: executionId
        };

        this.manualStatus[testBed.name] = {
          manualLock: testBed.manual_lock,
          manualLockExpiryTime: testBed.manual_lock_expiry_time,
          manualLockSubmitter: testBed.manual_lock_submitter
        };
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
          this.automationStatus[testBed.name] = {
            numExecutions: numExecutions,
            executionId: executionId,
            manualLock: manualLock
          };
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
              this.automationStatus[testBed.name] = {
                numExecutions: 1,
                executionId: automationStatus.internal_asset_in_use_suite_id, assetInUse: automationStatus.internal_asset
              };
            } else if (automationStatus.hasOwnProperty("used_by_suite_id")) {
              this.automationStatus[testBed.name] = {numExecutions: 1, executionId: automationStatus.used_by_suite_id};
            } else if (automationStatus.hasOwnProperty('suite_info') && automationStatus.suite_info) {
              this.automationStatus[testBed.name] = {
                numExecutions: 1,
                executionId: automationStatus.suite_info.suite_execution_id
              };
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
    let payload = {
      manual_lock_extension_hour: this.schedulingTime.hour,
      manual_lock_extension_minute: this.schedulingTime.minute
    };
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
    let payload = {
      manual_lock_submitter_email: this.selectedUser.email,
      manual_lock: true, manual_lock_extension_hour: this.schedulingTime.hour,
      manual_lock_extension_minute: this.schedulingTime.minute
    };
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

  edit(testBed) {
    testBed.editing_mode = true;
  }

  onSubmit(testBed) {
    let payload = {description: this.currentDescription};
    this.apiService.put('/api/v1/regression/test_beds/' + testBed.id, payload).subscribe((response) => {
      this.loggerService.success('Successfully updated!');
    }, error => {
      this.loggerService.error("Unable to update description");
    });
    this.currentDescription = "";
    testBed.editing_mode = false;
  }

  toggleEdit(testBed) {
    testBed.editing_mode = !testBed.editing_mode;
  }
}
