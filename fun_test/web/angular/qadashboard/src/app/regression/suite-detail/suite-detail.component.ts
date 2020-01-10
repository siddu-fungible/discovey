import {Component, OnDestroy, OnInit} from '@angular/core';
import { ApiService}  from "../../services/api/api.service";
import { ActivatedRoute } from "@angular/router";
import {ReRunService} from "../re-run.service";
import {LoggerService} from '../../services/logger/logger.service';
import {RegressionService} from "../regression.service";
import {CommonService} from "../../services/common/common.service";
import {NgbModal, ModalDismissReasons} from '@ng-bootstrap/ng-bootstrap';
import {UserService} from "../../services/user/user.service";
import {of} from "rxjs";
import {catchError, switchMap} from "rxjs/operators";
import {Title} from "@angular/platform-browser";


class Environment {
  BRANCH_FunOS: string = null;
  DISABLE_ASSERTIONS: boolean = null;
  RELEASE_BUILD: boolean = null;
}

@Component({
  selector: 'app-suite-detail',
  templateUrl: './suite-detail.component.html',
  styleUrls: ['./suite-detail.component.css']
})
export class SuiteDetailComponent implements OnInit, OnDestroy {
  logDir: any = null;
  suiteExecutionId: number;
  suiteExecution: any = null;
  scriptExecutionsMap: any = {};
  attributes: any;
  showReRunPanel: boolean = false;
  currenReRunHistory: any = null;
  currenReRunScriptInfo: any = null;
  testCaseInfo: any = {};
  scriptInfo: any = {};
  stateStringMap: any = null;
  stateMap: any = null;
  environment = new Environment();
  driver = null;
    // Re-run options
  reRunOptionsReRunFailed: boolean = false;
  reRunOptionsReRunAll: boolean = true;
  reUseBuildImage: boolean = false;
  reRunScript: string = null;
  refreshTimer: any = null;
  showingLogPath: boolean = false;
  showingInputs: boolean = false;
  showingEnvironment: boolean = false;
  ABSOLUTE_LOG_DIRECTORY = "/project/users/QA/regression/Integration/fun_test/web/static/logs/s_";

  constructor(private apiService: ApiService,
              private route: ActivatedRoute,
              private reRunService: ReRunService,
              private logger: LoggerService,
              private regressionService: RegressionService,
              private commonService: CommonService,
              private modalService: NgbModal,
              private title: Title) {
    this.stateStringMap = this.regressionService.stateStringMap;
    this.stateMap = this.regressionService.stateMap;
  }

  getHtmlLogPath(suiteExecutionId, path, logPrefix) {
    this.regressionService.getHtmlLogPath(suiteExecutionId, path, logPrefix);
  }

  getConsoleLogPath(suiteExecutionId, path, logPrefix) {
    this.regressionService.getConsoleLogPath(suiteExecutionId, path, logPrefix);
  }

  ngOnInit() {
    let self = this;


    this.driver = of(true).pipe(switchMap(response => {
      return this.getLogPath();
    }));
    this.driver.subscribe();

    this.route.params.subscribe(params => {
      if (params['suiteExecutionId']) {
        this.suiteExecutionId = params['suiteExecutionId'];
        let ctrl = this;
        this.apiService.get("/regression/suite_execution_attributes/" + this.suiteExecutionId).subscribe(result => {
          self.attributes = result.data;
          //self.attributes.unshift({"name": "Suite execution Id", "value": ctrl.suiteExecutionId});
          //let ctrl = this;
          this.apiService.get("/regression/suite_execution/" + this.suiteExecutionId).subscribe(function (result) {
            self.suiteExecution = result.data; // TODO: validate
            if (self.suiteExecution.fields.suite_path) {
              self.title.setTitle("Suite " + self.suiteExecutionId + ": " + self.suiteExecution.fields.suite_path);
            }
            ctrl.applyAdditionalAttributes(self.suiteExecution);
            ctrl.getReRunInfo(self.suiteExecution);

            //let suiteExecutionJson = JSON.parse(self.suiteExecution);
            let suiteFields = self.suiteExecution.fields;
            let testCaseExecutionIds = JSON.parse(suiteFields.test_case_execution_ids);

            if (self.suiteExecution.fields.hasOwnProperty("environment")) {
              let environment = JSON.parse(self.suiteExecution.fields.environment);
              //ctrl.environment.branchFunOs =
              if (environment.hasOwnProperty("build_parameters")) {
                let buildParameters = environment.build_parameters;
                if (buildParameters.hasOwnProperty('BRANCH_FunOS')) {
                  if (!buildParameters.BRANCH_FunOS) {
                    ctrl.environment.BRANCH_FunOS = "master"
                  } else {
                    ctrl.environment.BRANCH_FunOS = buildParameters.BRANCH_FunOS;
                  }
                }
                if (buildParameters.hasOwnProperty('DISABLE_ASSERTIONS')) {
                  ctrl.environment.DISABLE_ASSERTIONS = buildParameters.DISABLE_ASSERTIONS;
                }
                if (buildParameters.hasOwnProperty('RELEASE_BUILD')) {
                  ctrl.environment.RELEASE_BUILD = buildParameters.RELEASE_BUILD;
                }
              }

              if (environment.hasOwnProperty("with_stable_master")) {
                let withStableMaster = environment["with_stable_master"];
                if (withStableMaster.hasOwnProperty("debug") && withStableMaster.debug) {
                  ctrl.environment.RELEASE_BUILD = true;
                }
              }

            }
            for(let testCaseExecutionId of testCaseExecutionIds) {
              self.apiService.get('/regression/test_case_execution/' + self.suiteExecutionId + "/" + testCaseExecutionId).subscribe(function (result) {
                let data = result.data.execution_obj;
                let moreInfo = result.data.more_info;
                data.summary = moreInfo.summary;
                let scriptId = result.data.script_id;
                ctrl.fetchScriptInfo(scriptId, data.execution_id);

                if (!ctrl.scriptExecutionsMap.hasOwnProperty(scriptId)) {
                  ctrl.scriptExecutionsMap[scriptId] = {};
                }
                ctrl.scriptExecutionsMap[scriptId][data.execution_id] = data;
                ctrl.scriptExecutionsMap[scriptId][data.execution_id]["logPrefix"] = parseInt(data.log_prefix);

                let i = 0;
                ctrl.fetchTestCaseInfo(testCaseExecutionId);
              });
            }
            if (self.suiteExecution.fields.state >= self.stateMap.SUBMITTED) {
              self.refreshTimer = setInterval(() => {
                window.location.reload();
              }, 60 * 1000);
            }
          });
        });
      }
    });
  }


  getSuiteExecution(suiteExecutionId) {

  }


  getLogPath() {
    return this.apiService.get("/regression/log_path").pipe(switchMap(response => {
      this.logDir = response.data;
      return of(true)
    }), catchError (error => {
      this.logDir = "/static/logs/s_";
      return of(true);
    }));
  }

  fetchScriptInfo(scriptId, testCaseExecutionId) {
    this.regressionService.getScriptInfoById(scriptId).subscribe(response => {
      this.scriptInfo[scriptId] = response;
    });
  }

  getReRunInfo(suiteExecution) {
    if (suiteExecution.fields.suite_type === 'regular') {
      this.reRunService.getOriginalSuiteReRunInfo(suiteExecution.fields.execution_id).subscribe(response => {
      suiteExecution["reRunInfo"] = response;
      let i = 0;
      }, error => {

      })
    } else if (suiteExecution.fields.suite_type === 'dynamic') {
        this.reRunService.getReRunSuiteInfo(suiteExecution.fields.execution_id).subscribe(response => {
        suiteExecution["reRunInfo"] = response;
        }, error => {

        })
    }
  }


  parseInputs(inputs) {
    let parsedInputs = JSON.parse(inputs);
    let s = "";
    if (Object.keys(parsedInputs).length) {
      s = JSON.stringify(parsedInputs);
    }
    return s;
  }

  getKeys(map) {
    //console.log(map.keys());
    try {
      let a = Array.from(Object.keys(map));
      return a;
    } catch (e) {
      console.log(e);
    }
  }

  trimTime(t) {
    return t.replace(/\..*$/, "").replace(/T/, " ");
  }

  resultToClass(result): any {
    result = result.toUpperCase();
    let klass = "default";
    if (result === "FAILED") {
      klass = "danger";
    } else if (result === "PASSED") {
      klass = "success";
    } else if (result === "SKIPPED") {
      klass = "warning";
    } else if (result === "NOT_RUN") {
      klass = "default";
    } else if (result === "IN_PROGRESS") {
      klass = "info";
    } else if (result === "BLOCKED") {
      klass = "blocked";
    }
    return klass;
  }



  applyAdditionalAttributes(item) {
    item["showingDetails"] = false;
    item["showingInputs"] = false;
    item["showingEnvironment"] = false;
    if (item.hasOwnProperty('fields') && item.fields.hasOwnProperty('inputs')) {
      let inputs = JSON.parse(item.fields.inputs);
      item["parsedInputs"] = inputs;
    }

    if (item.hasOwnProperty('fields') && item.fields.hasOwnProperty('environment')) {
      let environment = JSON.parse(item.fields.environment);
      item["parsedEnvironment"] = environment;
    }

  }

  showDetailsClick(item) {
    item["showingDetails"] = !item["showingDetails"];
  }

  showInputsClick(item) {
    item["showingInputs"] = !item["showingInputs"];
  }

  showEnvironmentClick(item) {
    item["showingEnvironment"] = !item["showingEnvironment"];
  }

  getSchedulerLog(suiteId) {
    return this.regressionService.getSchedulerLog(suiteId);
  }

  getSchedulerLogDir(suiteId) {
    return this.regressionService.getSchedulerLogDir(suiteId);
  }


  reRunClick(suiteExecutionId, suitePath, resultFilter=null, scriptFilter=null, reUseBuildImage=null) {
    this.reRunService.submitReRun(suiteExecutionId, this.suiteExecution.fields.suite_id, resultFilter, scriptFilter, reUseBuildImage).subscribe(response => {
      alert("Re-run submitted");
      window.location.href = "/regression";
    }, error => {
      this.logger.error("Error submitting re-run");
    });
  }

  localizeTime(t) {
    return this.regressionService.getPrettyLocalizeTime(t);
  }

  hasReRuns(testCaseInfo) {
    let reRunHistory = JSON.parse(testCaseInfo.re_run_history);
    if (reRunHistory.length > 0) {
      let i = 0;
      reRunHistory.forEach(reRun => {
        //this.fetchTestCaseInfo(reRun.re_run_test_case_execution_id);
      });
    }
    return reRunHistory.length > 0;
  }

  getOriginalResult(testCaseInfo) {
    let reRunHistory = JSON.parse(testCaseInfo.re_run_history);
    let originalResult = "Unknown";
    for (let index = 0; index < reRunHistory.length; index++) {
      originalResult = reRunHistory[index].result;
      break;
    }
    return originalResult;
  }

  getLatestRerunEntry(testCaseInfo) {
    let entry = null;
    let reRunHistory = JSON.parse(testCaseInfo.re_run_history);
    if (reRunHistory.length > 0) {
      entry = reRunHistory[reRunHistory.length - 1];
    }
    return entry;
  }

  getLatestRerunSuiteExecutionId(testCaseInfo) {
    let suiteExecutionId = null;
    let reRunHistory = JSON.parse(testCaseInfo.re_run_history);
    if (reRunHistory.length > 0) {
      let lastEntry = reRunHistory[reRunHistory.length - 1];
      suiteExecutionId = lastEntry.re_run_suite_execution_id;
    }
    return suiteExecutionId;
  }

  setReRunInfo(testCaseInfo) {
    this.showReRunPanel = true;
    this.currenReRunScriptInfo = testCaseInfo;
    this.currenReRunHistory = JSON.parse(testCaseInfo.re_run_history);
    setTimeout(() => {
      this.commonService.scrollTo("re-run-panel");
    }, 2);

  }

  getReRunOriginalSuitePath(suiteExecution) {
    let suitePath = "*";
    if (suiteExecution) {
      if (suiteExecution.reRunInfo) {
        if (suiteExecution.reRunInfo.reRunInfo.length > 0) {
          suitePath = suiteExecution.reRunInfo.reRunInfo[0].original.attributes.suite_path;
        }
      }
    }
    return suitePath;
  }

  fetchTestCaseInfo(testCaseExecutionId) {
    if (this.testCaseInfo.hasOwnProperty(testCaseExecutionId)) {
      return true;
    } else {
      this.regressionService.getTestCaseExecution(testCaseExecutionId).subscribe((response) => {
        this.testCaseInfo[testCaseExecutionId] = response;
        let reRunHistory = JSON.parse(this.testCaseInfo[testCaseExecutionId].re_run_history);
        reRunHistory.forEach(reRun => {
          this.fetchTestCaseInfo(reRun.re_run_test_case_execution_id);
        })
      }, error => {
        this.logger.error(`Unable to fetch test case info for ${testCaseExecutionId}`);
      });
      return false;
    }
  }

  toInt(s) {
    return parseInt(s);
  }

  clickHistory(scriptId) {
    let url = "/regression/script_history_page/" + scriptId;
    window.open(url, '_blank');
  }

  /*
  scriptIdToPk(scriptId) {
    return this.scriptInfo[scriptId].pk;
  }*/

  killClick() {
    let suiteId = this.suiteExecutionId;
    this.regressionService.killSuite(this.suiteExecutionId).subscribe((result) => {
      this.logger.success(`Killed job: ${result}`);
      window.location.reload()
    }, error => {
      this.logger.error(`Unable kill ${suiteId}`);
    });
  }


  reRunModalOpen(content, scriptId=null) {
    this.reRunOptionsReRunFailed = false;
    this.reRunOptionsReRunAll = true;
    this.reUseBuildImage = false;
    this.reRunScript = scriptId;
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((suiteExecution) => {
      if (this.reRunOptionsReRunAll) {
        this.reRunClick(suiteExecution.fields.execution_id, suiteExecution.fields.suite_path, null, parseInt(scriptId), this.reUseBuildImage);
      }
      if (this.reRunOptionsReRunFailed) {
        this.reRunClick(suiteExecution.fields.execution_id, suiteExecution.fields.suite_path,['FAILED'], parseInt(scriptId), this.reUseBuildImage)
      }

    }, (reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    });
  }

  toggleReRunOptions() {
    this.reRunOptionsReRunAll = !this.reRunOptionsReRunAll;
    this.reRunOptionsReRunFailed = !this.reRunOptionsReRunFailed;
  }

  togglereUseBuildImage() {
    this.reUseBuildImage = !this.reUseBuildImage;
  }

  getScriptDetailLink(scriptId, executionId, logPrefix) {
    executionId = parseInt(executionId);
    return `/regression/script_detail/${scriptId}/${logPrefix}/${this.suiteExecutionId}`;
  }

  ngOnDestroy() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }

  getRunningTime() {
    let endTime = new Date();
    let startTime = null;
    if ((this.suiteExecution.fields.state == this.stateMap.IN_PROGRESS) || (this.suiteExecution.fields.state <= this.stateMap.COMPLETED)) {
      startTime = this.regressionService.convertToLocalTimezone(this.suiteExecution.fields.started_time);
    }
    if (this.suiteExecution.fields.state <= this.stateMap.COMPLETED) {
      endTime = this.regressionService.convertToLocalTimezone(this.suiteExecution.fields.completed_time);
    }
    let result = "";
    if (startTime) {
      let diffMs = endTime.getTime() - startTime.getTime();
      result = this.commonService.milliSecondsElapsedToDays(diffMs);
    }
    return result;
    //return
  }

  onTogglePreserveLogs(preserveLogs) {
    this.suiteExecution.fields.preserve_logs = !this.suiteExecution.fields.preserve_logs;
    this.regressionService.preserveLogs(this.suiteExecution.fields.execution_id, this.suiteExecution.fields.preserve_logs).subscribe(response => {

    }, error => {
      this.logger.error("Unable to modify preserve logs");
    })

  }

  onTogglePauseOnFailure(pauseOnFailure) {
    this.suiteExecution.fields.pause_on_failure = pauseOnFailure;
    this.regressionService.pauseOnFailure(this.suiteExecution.fields.execution_id, this.suiteExecution.fields.pause_on_failure).subscribe(response => {

    }, error => {
      this.logger.error("Unable to modify pause on failure");
    })

  }
}
