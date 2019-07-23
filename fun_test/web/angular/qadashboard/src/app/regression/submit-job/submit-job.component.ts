
import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {Title} from "@angular/platform-browser";
import {Sort} from "@angular/material";
import {Validators} from "@angular/forms";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'app-submit-job',
  templateUrl: './submit-job.component.html',
  styleUrls: ['./submit-job.component.css'],
  animations:    [trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(300)
      ]),
      transition(':leave', [
        animate(1, style({ opacity: 1.0 }))
      ]),
      state('*', style({ opacity: 1.0 })),
    ])]
})
export class SubmitJobComponent implements OnInit {
  DEFAULT_TEST_BED: string = "fs-6";
  scheduleInMinutes: number;
  scheduleInMinutesRadio: boolean;
  buildUrl: string;
  selectedSuite: string = null;
  selectedInfo: any;
  jobId: number;
  suitesInfo: any;
  selectedTags: any[] = [];
  tags: any;
  emailOnFailOnly: boolean;
  schedulingOptions: boolean;
  scheduleInMinutesRepeat: any;
  scheduleAt: any;
  scheduleAtRepeat: any;
  emails: any;
  suitesInfoKeys: any = [];
  selectTags: any[] = [];
  dropdownSettings = {};
  schedulingType:number = 1; //{ options: 'periodic' };
  schedulingTime = {hour: 0, minute: 1};
  todaySchedulingTimeRepeatInMinutesOption: boolean = false;
  todaySchedulingTimeRepeatInMinutesValue = 60;
  schedulingTimeTimezone = "IST";
  daysOptions = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  selectedDays: string[] = [];
  selectedTestBedType: string = this.DEFAULT_TEST_BED;
  testBedTypes: any = null;
  testBedNames: string[] = [];
  submitting: string = null;
  tftpImagePath: string = "stable-funos-f1.stripped.gz";
  // bootArgs: string = "app=hw_hsu_test --dpc-server --dpc-uart --csr-replay --serdesinit --all_100g";
  bootArgs: string = "";

  withJenkinsBuild: boolean = true;

  disableAssertions: boolean = true;
  funOsMakeFlags: string = null;
  branchFunOs: string = null;
  branchFunSdk: string = null;
  branchFunControlPlane: string = null;
  branchFunHw: string = null;
  skipDasmC: boolean = true;
  branchFunTools: string = null;

  selectedScriptPk: number = null;
  resetScriptSelector: boolean = false;
  privateFunosTgzUrl: string = null;

  suiteSelectionMode: string = "BY_SUITE";
  selectedUser: any = null;
  users: any = null;
  BOOT_ARGS_REPLACEMENT_STRING: string = "rpl_:";
  description: string = null;
  type: string = "suite"; // some other type like task
  queryParams: any = null;
  jobInputs: string = null; // input dictionary to be sent to the scheduler

  moreJenkinsOptions: boolean = false;


  constructor(private apiService: ApiService, private logger: LoggerService,
              private title: Title, private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.title.setTitle('Submit Jobs');
    this.dropdownSettings = {
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      itemsShowLimit: 3,
      allowSearchFilter: true
    };
    this.scheduleInMinutes = 1;
    this.scheduleAtRepeat = false;
    this.scheduleInMinutesRepeat = null;
    this.selectTags = [];
    this.scheduleAt = null;
    this.scheduleInMinutesRadio = true;
    this.buildUrl = "http://dochub.fungible.local/doc/jenkins/funsdk/latest/";
    this.selectedSuite = null;
    this.selectedInfo = null;
    this.schedulingOptions = false;
    this.jobId = null;
    let self = this;
    this.getQueryParam().subscribe((response) => {
      this.queryParams = response;
      let queryParamString = "";
      if (this.type === "task") {
        queryParamString = "?suite_type=task";
      }
      this.apiService.get("/regression/suites" + queryParamString).subscribe((result) => {
        let suitesInfo = result.data;
        self.suitesInfo = suitesInfo;

        for (let suites of Object.keys(suitesInfo)) {
          self.suitesInfoKeys.push(suites);
        }
        self.suitesInfoKeys.sort();
      });

    });

    this.selectedTags = [];
    this.tags = [];
    this.fetchUsers();
    this.fetchTags();
    this.fetchTestBeds();
    this.emailOnFailOnly = false;
  }

  getQueryParam() {
    return this.route.queryParams.pipe(switchMap(params => {
      if (params.hasOwnProperty('type')) {
        this.type = params["type"];
      }
      return of(params);
    }))
  }


  onItemSelect (item:any): void {
    console.log(item);
  }
  onSelectAll (items: any): void {
    console.log(items);
  }

  fetchUsers(): void {
    this.apiService.get("/api/v1/users").subscribe(response => {
      this.users = response.data;
    }, error => {
      this.logger.error("Unable to fetch users");
    })
  }


  fetchTestBeds(): void {
    this.apiService.get('/regression/testbeds').subscribe(response => {
      this.testBedTypes = response.data;
      Object.keys(this.testBedTypes).map(key => {
        this.testBedNames.push(key);
        this.testBedNames.sort();
        this.selectedTestBedType = this.DEFAULT_TEST_BED;
      })

    })
  }

  fetchTags(): void {
    let self = this;
    this.apiService.get('/regression/tags').subscribe(function (result) {
      let data = JSON.parse(result.data);
      let i = 1;
      self.selectTags = [];
      for (let item of data) {
        self.tags.push({name: item.fields.tag});
        self.selectTags.push({item_id: i++, item_text: item.fields.tag});
      }
      //self.selectedTags = self.tags
    }, error => {
      this.logger.error("unable to fetch tags");
    });
  }

  changedValue(selectedSuite) {
    this.selectedInfo = this.suitesInfo[selectedSuite];
    this.selectedScriptPk = null;
    this.resetScriptSelector = true;
  }

  parseScriptInfo(scriptInfo) {
    let s = "";
    if (scriptInfo.hasOwnProperty('path')) {
      s = scriptInfo.path;
      if (scriptInfo.hasOwnProperty('inputs')) {
        s = s + " Inputs: " + JSON.stringify(scriptInfo.inputs);
      }
    } else if (scriptInfo.hasOwnProperty('info')) {
      s = "Tags: " + scriptInfo.info.tags;
    }
    return s;
  }

  getSchedulingOptions(payload) {
    if (this.schedulingOptions) {
      if (this.schedulingType === 2) {
        payload["scheduling_type"] = "today";
        if (this.todaySchedulingTimeRepeatInMinutesOption) {
          if (!this.todaySchedulingTimeRepeatInMinutesValue) {
            this.logger.error("Please enter the repeat in minutes value");
            return null;
          } else {
            payload["repeat_in_minutes"] = this.todaySchedulingTimeRepeatInMinutesValue;
          }
        }

      } else if (this.schedulingType === 3) {
        payload["scheduling_type"] = "periodic";
        if (this.selectedDays.length === 0) {
          this.logger.error("Please select at least one day");
          return null;
        } else {
          payload["requested_days"] = this.selectedDays;
          payload["build_url"] = null;
        }
      }
    }
    payload["requested_hour"] = this.schedulingTime.hour;
    payload["requested_minute"] = this.schedulingTime.minute;
    payload["timezone"] = this.schedulingTimeTimezone;
    return payload;
  }

  _getSelectedtags() {
    let tags = [];
    this.selectedTags.forEach(function (item) {
      tags.push(item.item_text);
    });
    return tags;
  }


  submitClick() {
    let self = this;
    this.jobId = null;
    let payload = {};
    if (this.suiteSelectionMode === 'BY_SUITE') {
      payload["suite_path"] = this.selectedSuite;
    } else {
      payload["script_pk"] = this.selectedScriptPk;
    }

    if (!this.selectedUser) {
      return this.logger.error("Please select a user");
    }
    payload["build_url"] = this.buildUrl;
    payload["tags"] = this._getSelectedtags();
    payload["email_on_fail_only"] = this.emailOnFailOnly;
    payload["test_bed_type"] = this.selectedTestBedType;
    payload["submitter_email"] = this.selectedUser.email;
    if (this.type) {
      payload["type"] = this.type;
    }
    if (this.emails) {
      this.emails = this.emails.split(",");
      payload["email_list"] = this.emails
    }
    payload["scheduling_type"] = "asap";
    if (this.schedulingOptions) {
      payload = this.getSchedulingOptions(payload);
      if (!payload) {
        return;
      }
    }
    payload["environment"] = {};


    if (this.selectedTestBedType) {
      payload["environment"]["test_bed_type"] = this.selectedTestBedType; //TODO: this is not needed after scheduler_v2
    }


    if (this.isTestBedFs()) {
      if (!this.withJenkinsBuild) {
        if (this.tftpImagePath && this.tftpImagePath !== "") {
          payload["environment"]["tftp_image_path"] = this.tftpImagePath;
        }
      } else {
      payload["environment"]["with_jenkins_build"] = true;
      }

      if (payload["environment"]["with_jenkins_build"]) {
        payload["environment"]["build_parameters"] = {};
        if (this.bootArgs && this.bootArgs !== "" && this.isTestBedFs()) {
          payload["environment"]["build_parameters"]["BOOTARGS"] = this.bootArgs.replace(/\s+/g, this.BOOT_ARGS_REPLACEMENT_STRING);
        }
        payload["environment"]["build_parameters"]["DISABLE_ASSERTIONS"] = this.disableAssertions;
        payload["environment"]["build_parameters"]["FUNOS_MAKEFLAGS"] = this.funOsMakeFlags;
        payload["environment"]["build_parameters"]["BRANCH_FunOS"] = this.branchFunOs;
        payload["environment"]["build_parameters"]["BRANCH_FunSDK"] = this.branchFunSdk;
        payload["environment"]["build_parameters"]["BRANCH_FunControlPlane"] = this.branchFunControlPlane;
        payload["environment"]["build_parameters"]["SKIP_DASM_C"] = this.skipDasmC;
        payload["environment"]["build_parameters"]["BRANCH_FunTools"] = this.branchFunTools;
        payload["environment"]["build_parameters"]["BRANCH_FunHW"] = this.branchFunHw;
      }
    }

    if (this.jobInputs) {
      payload["job_inputs"] = this.jobInputs;
    }

    if (this.privateFunosTgzUrl && this.privateFunosTgzUrl !== "") {
      payload["environment"]["private_funos_tgz_url"] = this.privateFunosTgzUrl;
    }

    if (this.description) {
      payload["description"] = this.description;
    }

    this.submitting = "Submitting job";
    let ctrl = this;
    this.apiService.post('/regression/submit_job', payload).subscribe(function (result) {
      self.jobId = parseInt(result.data);
      window.location.href = "/regression/suite_detail/" + self.jobId;
      ctrl.logger.success(`Job: ${self.jobId} Submitted`);
      console.log("Job: " + self.jobId + " Submitted");
      ctrl.submitting = null;
    }, error => {
      self.logger.error("Unable to submit job");
      ctrl.submitting = null;
    });
  }

  singleSelectPkEvent(pk) {
    console.log("Pk: " + pk);
    this.selectedSuite = "";
    this.selectedInfo = null;
    this.selectedScriptPk = pk;
  }

  toggleWithJenkins() {
    this.withJenkinsBuild = !this.withJenkinsBuild;
  }



  isTestBedFs(): boolean {
    let result = null;
    if (this.selectedTestBedType) {
      result = this.selectedTestBedType.indexOf('fs') > -1 || this.selectedTestBedType.indexOf('suite-based') > -1;
    }
    return result;
  }

  jobInputsChanged(jobInputs) {
    this.jobInputs = jobInputs;
  }



}
