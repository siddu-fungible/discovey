
import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {Title} from "@angular/platform-browser";
import {Sort} from "@angular/material";
import {Validators} from "@angular/forms";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {switchMap} from "rxjs/operators";
import {Observable, of} from "rxjs";
import {ActivatedRoute} from "@angular/router";
import {TriageService} from "../triage2/triage.service";
import {SuiteEditorService} from "../suite-editor/suite-editor.service";
import {CommonService} from "../../services/common/common.service";
import {TestBedService} from "../test-bed/test-bed.service";
import {RegressionService} from "../regression.service";
import {SavedJobConfigs} from "../definitions";
import {showAnimation} from "../../animations/generic-animations";
import {UserProfile} from "../../login/definitions";

class Mode {
  static REGULAR = "REGULAR";
  static TASK = "TASK";
  static TRIAGE = "TRIAGE"
}

class BuildType {
  static TFTP_IMAGE_PATH = "TFTP_IMAGE_PATH";
  static WITH_JENKINS_BUILD = "WITH_JENKINS_BUILD";
  static WITH_STABLE_MASTER = "WITH_STABLE_MASTER";
  static USE_BUNDLE_IMAGE = "USE_BUNDLE_IMAGE";
}


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
    ]), showAnimation]
})
export class SubmitJobComponent implements OnInit {
  DEFAULT_TEST_BED: string = "fs-6";
  scheduleInMinutes: number;
  scheduleInMinutesRadio: boolean;
  buildUrl: string;
  selectedSuite: any = null;
  //selectedInfo: any;
  availableCategories: string [] = null;
  selectedCategories: string [] = null;
  byNameSearchText: string = null;

  jobId: number;
  suitesInfo: any;
  selectedTags: any[] = [];
  releaseTrains: string [] = [];
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
  savedJobUrl: string = "";


  funOsMakeFlags: string = null;
  branchFunOs: string = null;
  branchFunSdk: string = null;
  branchFunControlPlane: string = null;
  branchFunHw: string = null;
  skipDasmC: boolean = true;
  branchFunTools: string = null;
  branchFunJenkins: string = null;
  branchFungibleHostDrivers: string = null;
  releaseBuild: boolean = true;

  selectedScriptPk: number = null;
  selectedScriptPath: string = null;
  resetScriptSelector: boolean = false;
  privateFunosTgzUrl: string = null;

  suiteSelectionMode: string = "BY_SUITE";
  users: any = null;
  BOOT_ARGS_REPLACEMENT_STRING: string = "rpl_:";
  description: string = null;
  //type: string = "regular"; // some other type like task
  queryParams: any = null;
  jobInputs: string = null; // input dictionary to be sent to the scheduler
  richBootArgs: string = null;
  csiPerf: boolean = false;
  csiCacheMiss: boolean = false;
  dryRun: boolean = false;
  hbmDump: boolean = false;
  pauseOnFailure: boolean = false;
  moreJenkinsOptions: boolean = false;
  mode: Mode = Mode.REGULAR;
  Mode = Mode;
  BuildType = BuildType;
  buildType: BuildType = BuildType.WITH_JENKINS_BUILD;
  usingSavedConfig: boolean = false;
  savedConfigSuiteId: number = null;
  savedConfigSuiteName: string = null;

  // For Triaging
  triageTypes = [{value: 6, description: "Pass or Fail"}, {value: 7, description: "Regex match"}];  //Taken from TriagingTypes
  gitShasValid: boolean = false;
  validateShasStatus: string = null;
  fromFunOsSha: string = ""; //"8751993af1b24e8159a5f2f3fc22480c44fde8c6";
  toFunOsSha: string = ""; //"74e24c8210d8c2ffb09712f9924eb959201dcf46";
  commitsInBetween: string[] = [];
  currentTriageType: number = null;
  regexMatchString: string = null;

  userProfile: UserProfile = null;

  withStableMaster = {debug: false, stripped: true};
  bundleImageParameters = {release_train: null, build_number: "latest"};
  constructor(private apiService: ApiService, private logger: LoggerService,
              private title: Title, private route: ActivatedRoute,
              private triageService: TriageService,
              private suiteEditorService: SuiteEditorService,
              private commonService: CommonService,
              private testBedService: TestBedService,
              private regressionService: RegressionService) {
    this.currentTriageType = this.triageTypes[0].value;
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
    //this.selectedInfo = null;
    this.schedulingOptions = false;
    this.jobId = null;
    let self = this;
    this.userProfile = this.commonService.getUserProfile();
    if (!this.userProfile) {
      this.logger.error("Unable to fetch user profile");
      return;
    }
    this.getQueryParam().subscribe((response) => {
      this.queryParams = response;
      let queryParamString = "";
      if (this.mode === Mode.TASK) {
        queryParamString = "?suite_type=task";
      }

    });

    this.selectedTags = [];
    this.tags = [];
    this.fetchUsers();
    this.fetchTags();
    this.fetchReleaseTrains();
    this.fetchTestBeds();
    this.fetchSuites();
    this.emailOnFailOnly = false;
    this.selectedTestBedType = this.DEFAULT_TEST_BED;

  }

  fetchSuites() {
    of(true).pipe(switchMap(response => {
      return this.suiteEditorService.categories();
    })).pipe(switchMap(response => {
      this.availableCategories = response;
      return this.suiteEditorService.suites(null, 400, 1, this.selectedCategories, this.byNameSearchText);
    })).pipe(switchMap(response => {
      this.suitesInfo = response;
      return of(true)
    })).subscribe(() => {
    }, error => {
      this.logger.error("Unable to fetch suites");
    })
  }


  getQueryParam() {
    return this.route.queryParams.pipe(switchMap(params => {
      if (params.hasOwnProperty('mode')) {
        this.mode = params["mode"];
        if (this.mode === Mode.TRIAGE) {
          this.dryRun = true;
        }
      }
      if (params.hasOwnProperty('saved_job_config')) {
        let savedJobId = parseInt(params["saved_job_config"]);
        this.usingSavedConfig = true;
        this.fetchSavedJobConfig(savedJobId);

      }
      return of(params);
    }))
  }

  fetchSavedJobConfig(id) {
    let savedJobConfig = new SavedJobConfigs();
    savedJobConfig.get(savedJobConfig.getUrl({id: id})).subscribe(response => {
      let payload = response.config;
      // auto populate
      this.selectedTestBedType = payload.test_bed_type;
      this.buildUrl = payload.build_url;
      this.schedulingType = payload.scheduling_type;
      this.emailOnFailOnly = payload.email_on_fail_only;

      let payloadEnvironment = payload.environment;
      if (payloadEnvironment.hasOwnProperty('tftp_image_path')) {
        this.buildType = this.BuildType.TFTP_IMAGE_PATH;
      }

      if (payloadEnvironment.hasOwnProperty('bundle_image_parameters')) {
        this.buildType = this.BuildType.USE_BUNDLE_IMAGE;
        this.bundleImageParameters.release_train = payloadEnvironment.bundle_image_parameters.release_train;
        this.bundleImageParameters.build_number = payloadEnvironment.bundle_image_parameters.build_number;
      }

      if (payloadEnvironment.hasOwnProperty('with_stable_master')) {
        this.buildType = this.BuildType.WITH_STABLE_MASTER;
        this.withStableMaster.debug = payloadEnvironment.with_stable_master.debug;
        this.withStableMaster.stripped = payloadEnvironment.with_stable_master.stripped;
      }

      if (payloadEnvironment.hasOwnProperty('with_jenkins_build')) {
        this.buildType = this.BuildType.WITH_JENKINS_BUILD;
        let buildParameters = payloadEnvironment.build_parameters;
        if (buildParameters.hasOwnProperty('RELEASE_BUILD')) {
          this.releaseBuild = buildParameters.RELEASE_BUILD;
        }
        if (buildParameters.hasOwnProperty('FUNOS_MAKEFLAGS')) {
          this.funOsMakeFlags = buildParameters.FUNOS_MAKEFLAGS;
        }
        if (buildParameters.hasOwnProperty('BRANCH_FunOS')) {
          this.branchFunOs = buildParameters.BRANCH_FunOS;
        }
        if (buildParameters.hasOwnProperty('BRANCH_FunSDK')) {
          this.branchFunSdk = buildParameters.BRANCH_FunSDK;
        }
        if (buildParameters.hasOwnProperty('BRANCH_FunControlPlane')) {
          this.branchFunControlPlane = buildParameters.BRANCH_FunControlPlane;
        }
        if (buildParameters.hasOwnProperty('SKIP_DASM_C')) {
          this.skipDasmC = buildParameters.SKIP_DASM_C;
        }
        if (buildParameters.hasOwnProperty('BRANCH_FunTools')) {
          this.branchFunTools = buildParameters.BRANCH_FunTools;
        }
        if (buildParameters.hasOwnProperty('BRANCH_FunHW')) {
          this.branchFunHw = buildParameters.BRANCH_FunHW;
        }
        if (buildParameters.hasOwnProperty('BRANCH_FunJenkins')) {
          this.branchFunJenkins = buildParameters.BRANCH_FunJenkins;
        }
        if (buildParameters.hasOwnProperty('BRANCH_fungible_host_drivers')) {
          this.branchFungibleHostDrivers = buildParameters.BRANCH_fungible_host_drivers;
        }
      }

      if (payloadEnvironment.hasOwnProperty('private_funos_tgz_url')) {
        this.privateFunosTgzUrl = payloadEnvironment.private_funos_tgz_url;
      }


      if (payload.hasOwnProperty('job_inputs')) {
        this.jobInputs = payload.job_inputs;
      }

      if (payload.hasOwnProperty('rich_inputs')) {
        this.richBootArgs = payload.rich_inputs;
      }

      if (payloadEnvironment.hasOwnProperty('csi_perf')) {
        this.csiPerf = payloadEnvironment.csi_perf;
      }

      if (payloadEnvironment.hasOwnProperty('csi_cache_miss')) {
        this.csiCacheMiss = payloadEnvironment.csi_cache_miss;
      }

      if (payloadEnvironment.hasOwnProperty('dry_run')) {
        this.dryRun = payloadEnvironment.dry_run;
      }

      if (payloadEnvironment.hasOwnProperty('hbm_dump')) {
        this.hbmDump = payloadEnvironment.hbm_dump;
      }

      if (payload.hasOwnProperty('pauseOnFailure')) {
        this.pauseOnFailure = payload.pauseOnFailure;
      }

      if (payload.hasOwnProperty('description')) {
        this.description = payload.description;
      }

      if (payload.hasOwnProperty('suite_id') && (payload.suite_id)) {
        this.savedConfigSuiteId = payload.suite_id;
        if (payload.hasOwnProperty('saved_suite_name'))  {
          this.savedConfigSuiteName = payload.saved_suite_name;
        }
      } else if (payload.hasOwnProperty('script_pk')) {
        this.selectedScriptPk = payload.script_pk;
        if (payload.hasOwnProperty('saved_script_path')) {
          this.selectedScriptPath = payload.saved_script_path;
        }
      }

      let i = 0;
    }, error => {
      this.logger.error(`Unable to fetch saved job config`, error);
    })
  }

  validateShas() {
    if ((!this.fromFunOsSha) || (!this.toFunOsSha)) {
      return this.logger.error("Git commits are invalid");
    }
    let url = "/api/v1/git_commits_fun_os/" + this.fromFunOsSha + "/" + this.toFunOsSha;
    this.validateShasStatus = "Validating commits";
    this.apiService.get(url).subscribe((response) => {
      this.commitsInBetween = response.data;
      if (this.commitsInBetween && this.commitsInBetween.length) {
        this.gitShasValid = true;
        this.validateShasStatus = null;

      }
    }, error => {
      this.logger.error("Git commits are invalid");
      this.validateShasStatus = null;

    })
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

      })

    })
  }

  fetchReleaseTrains(): void {
    this.regressionService.releaseTrains().subscribe(result => {
      this.releaseTrains = result;
    }, error => {
      this.logger.error("Unable to fetch release trains");
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
    this.selectedSuite = selectedSuite;
    this.selectedScriptPk = null;
    this.resetScriptSelector = true;
    setTimeout(() => {
      this.commonService.scrollTo("suite-info");
    }, 500);

  }

  _listToString(l) {
    let s = "";
    if (l) {
      l.forEach(listElement => {
        s += listElement + ",";
      });
      s = s.replace(/,$/, "");
    }

    return s;
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


  submitClick(saveConfiguration?) {

    let self = this;

    this.jobId = null;
    let payload = {};

    if (!this.usingSavedConfig) {
      if (this.suiteSelectionMode === 'BY_SUITE') {
        payload["suite_id"] = this.selectedSuite.id;
        if (this.selectedSuite.name === "storage_sanity.json") {
          this.selectedTestBedType = "fs-6";
        }
      } else {
        payload["script_pk"] = this.selectedScriptPk;
      }

    } else {
      if (this.savedConfigSuiteId) {
        payload["suite_id"] = this.savedConfigSuiteId;
      } else {
        payload["script_pk"] = this.selectedScriptPk;
      }

    }

    if (!this.userProfile) {
      return this.logger.error("Please select a user");
    }
    payload["build_url"] = this.buildUrl;
    payload["tags"] = this._getSelectedtags();
    payload["email_on_fail_only"] = this.emailOnFailOnly;
    payload["test_bed_type"] = this.selectedTestBedType;
    payload["submitter_email"] = this.userProfile.user.email;
    payload["pause_on_failure"] = this.pauseOnFailure;

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
      if (this.buildType === this.BuildType.TFTP_IMAGE_PATH) {
        if (this.tftpImagePath && this.tftpImagePath !== "") {
          payload["environment"]["tftp_image_path"] = this.tftpImagePath;
        }
      } else if (this.buildType === this.BuildType.USE_BUNDLE_IMAGE) {
        if (this.bundleImageParameters.release_train === null) {
          return this.logger.error("Please select bundle release");
        }
        if (!this.bundleImageParameters.build_number) {
          return this.logger.error("Please select bundle number");
        }
        payload["environment"]["bundle_image_parameters"] = this.bundleImageParameters;
      } else if (this.buildType === this.BuildType.WITH_JENKINS_BUILD) {
        payload["environment"]["with_jenkins_build"] = true;
      } else if (this.buildType === this.BuildType.WITH_STABLE_MASTER) {
        payload["environment"]["with_stable_master"] = this.withStableMaster;
      }

      if (payload["environment"]["with_jenkins_build"]) {
        payload["environment"]["build_parameters"] = {};
        if (this.bootArgs && this.bootArgs !== "" && this.isTestBedFs()) {
          payload["environment"]["build_parameters"]["BOOTARGS"] = this.bootArgs.replace(/\s+/g, this.BOOT_ARGS_REPLACEMENT_STRING);
        }
        payload["environment"]["build_parameters"]["RELEASE_BUILD"] = this.releaseBuild;
        payload["environment"]["build_parameters"]["FUNOS_MAKEFLAGS"] = this.funOsMakeFlags;
        payload["environment"]["build_parameters"]["BRANCH_FunOS"] = this.branchFunOs;
        payload["environment"]["build_parameters"]["BRANCH_FunSDK"] = this.branchFunSdk;
        payload["environment"]["build_parameters"]["BRANCH_FunControlPlane"] = this.branchFunControlPlane;
        payload["environment"]["build_parameters"]["SKIP_DASM_C"] = this.skipDasmC;
        payload["environment"]["build_parameters"]["BRANCH_FunTools"] = this.branchFunTools;
        payload["environment"]["build_parameters"]["BRANCH_FunHW"] = this.branchFunHw;
        payload["environment"]["build_parameters"]["BRANCH_FunJenkins"] = this.branchFunJenkins;
        payload["environment"]["build_parameters"]["BRANCH_fungible_host_drivers"] = this.branchFungibleHostDrivers;

      }
    }

    if (this.jobInputs) {
      payload["job_inputs"] = this.jobInputs;
    }


    if (this.privateFunosTgzUrl && this.privateFunosTgzUrl !== "") {
      payload["environment"]["private_funos_tgz_url"] = this.privateFunosTgzUrl;
    }

    if (this.richBootArgs) {
      payload["rich_inputs"] = {boot_args: this.richBootArgs};
    }

    if (this.csiPerf) {
      payload["environment"]["csi_perf"] = this.csiPerf;
    }

    if (this.csiCacheMiss) {
      payload["environment"]["csi_cache_miss"] = this.csiCacheMiss;
    }


    if (this.dryRun) {
      payload["environment"]["dry_run"] = this.dryRun;
    }

    if (this.hbmDump) {
      payload["environment"]["hbm_dump"] = this.hbmDump;
    }

    if (this.description) {
      payload["description"] = this.description;
    }

    if (this.mode === Mode.TRIAGE) {
      if (!this.fromFunOsSha || !this.toFunOsSha) {
        this.logger.error("Please fill both From & To FunOS commit");
        return;
      }
      this.submitting = "Submitting triage";
      let ctrl = this;
      this.triageService.add(this.currentTriageType,
        this.regexMatchString,
        this.fromFunOsSha,
        this.toFunOsSha,
        this.userProfile.user.email, payload).subscribe((response) => {
          ctrl.submitting = null;
          this.logger.success("Submitted triage");
          let triageId = response;
          if (triageId > 0) {
            window.location.href = "regression/triaging/" + triageId;
          }

      }, error => {
          this.logger.error("Error submitting triage: " + error);
          ctrl.submitting = null;
      });
    }

    if (this.mode === Mode.REGULAR && !saveConfiguration) {
      this.submitting = "Submitting job";
      let ctrl = this;
      this.apiService.post('/regression/submit_job', payload).subscribe(function (result) {
        self.jobId = parseInt(result.data);
        window.location.href = "/regression/suite_detail/" + self.jobId;
        if (ctrl.selectedTestBedType.length > 1) {
          window.location.href = "/regression";
        }
        ctrl.logger.success(`Job: ${self.jobId} Submitted`);
        console.log("Job: " + self.jobId + " Submitted");
        ctrl.submitting = null;
      }, error => {
        self.logger.error("Unable to submit job");
        ctrl.submitting = null;
      });
    }
    if (saveConfiguration) {
      let savedJobConfigObject = new SavedJobConfigs();
      savedJobConfigObject.config = payload;
      if (this.selectedSuite) {
        savedJobConfigObject.config["saved_suite_id"] = this.selectedSuite.id;
        savedJobConfigObject.config["saved_suite_name"] = this.selectedSuite.name;
      } else if (this.selectedScriptPk) {
        savedJobConfigObject.config["saved_script_path"] = this.selectedScriptPath;
      }

      savedJobConfigObject.create(savedJobConfigObject.url, savedJobConfigObject.serialize()).subscribe(response => {
        this.savedJobUrl = `${window.location.origin}/regression/submit_job_page?saved_job_config=${savedJobConfigObject.id}`;
      }, error => {
        this.logger.error(`Unable to save configuration`);
      })
    }

  }

  singleSelectPkEvent(pk) {
    console.log("Pk: " + pk);
    this.selectedSuite = null;
    this.selectedScriptPk = pk;
  }

  singleSelectScriptPathEvent(scriptPath) {
    this.selectedScriptPath = scriptPath;
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

  jobBootArgsChanged(bootArgs) {
    this.richBootArgs = bootArgs;
  }

  test() {
    console.log(this.selectedTestBedType);
  }

  _hasKey(o, key) {
    return Object.keys(o).indexOf(key) > -1;
  }

  _getPoolMemberTypeOptionsString(assetType, poolMemberTypeOptions) {
    let s = "";
    Object.keys(poolMemberTypeOptions).forEach(poolMemberTypeOption => {
      let optionTypeString = this.testBedService.poolMemberTypeOptionToString(assetType, poolMemberTypeOption);
      s += `${optionTypeString}: ${poolMemberTypeOptions[poolMemberTypeOption].num}, `;
    });
    s = s.replace(/, $/, "");
    return s;
  }

  onChangeSelectedCategories() {
    this.fetchSuites();
  }

  onSearchText(searchText) {
    this.byNameSearchText = searchText;
    this.fetchSuites();
  }

  toggleCsiCacheMiss() {
    this.csiCacheMiss = !this.csiCacheMiss;

    if (this.csiCacheMiss) {
      this.csiPerf = false;
    }
  }

  toggleCsiPerf() {
    this.csiPerf = !this.csiPerf;
    if (this.csiPerf) {
      this.csiCacheMiss = false;
    }
  }

  dismissSavedJobUrl() {
    this.savedJobUrl = null;
  }

  /*test() {
    console.log(this.selectedTestBedType);
  }*/

}
