import { Component, OnInit } from '@angular/core';
import { ApiService}  from "../../services/api/api.service";
import { ActivatedRoute } from "@angular/router";
import {hasOwnProperty} from "tslint/lib/utils";
import {ReRunService} from "../re-run.service";
import {LoggerService} from '../../services/logger/logger.service';
import {RegressionService} from "../regression.service";
import {CommonService} from "../../services/common/common.service";


class Environment {
  BRANCH_FunOS: string = null;
  DISABLE_ASSERTIONS: boolean = null;
}

@Component({
  selector: 'app-suite-detail',
  templateUrl: './suite-detail.component.html',
  styleUrls: ['./suite-detail.component.css']
})
export class SuiteDetailComponent implements OnInit {
  logDir: any;
  CONSOLE_LOG_EXTENSION: string;
  HTML_LOG_EXTENSION: string;
  executionId: number;
  suiteExecution: any = null;
  testCaseExecutions: any;
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

  constructor(private apiService: ApiService, private route: ActivatedRoute, private reRunService: ReRunService, private logger: LoggerService, private regressionService: RegressionService, private commonService: CommonService) {
    this.stateStringMap = this.regressionService.stateStringMap;
    this.stateMap = this.regressionService.stateMap;
  }

  ngOnInit() {
    let self = this;
    this.route.params.subscribe(params => {
      if (params['suiteId']) {
        this.executionId = params['suiteId'];
        let ctrl = this;
        this.apiService.get("/regression/suite_execution_attributes/" + this.executionId).subscribe(result => {
          self.attributes = result.data;
          self.attributes.unshift({"name": "Suite execution Id", "value": ctrl.executionId});
        });
      }
    });
    this.logDir = null;
    this.CONSOLE_LOG_EXTENSION = ".logs.txt";  //TIED to scheduler_helper.py  TODO
    this.HTML_LOG_EXTENSION = ".html";         //TIED to scheduler_helper.py  TODO
    if (!this.logDir) {
      this.apiService.get("/regression/log_path").subscribe(function (result) {
        self.logDir = result.data;
      }, error => {
        self.logDir = "/static/logs/s_";
      });
    }
    let ctrl = this;
    this.testCaseExecutions = [];
    this.apiService.get("/regression/suite_execution/" + this.executionId).subscribe(function (result) {
      self.suiteExecution = result.data; // TODO: validate
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

        }
      }
      for(let testCaseExecutionId of testCaseExecutionIds) {
        self.apiService.get('/regression/test_case_execution/' + self.executionId + "/" + testCaseExecutionId).subscribe(function (result) {
          //self.testCaseExecutions.push(JSON.parse(result.data)[0]);
          let data = result.data.execution_obj;
          let moreInfo = result.data.more_info;
          data.summary = moreInfo.summary;
          self.testCaseExecutions.push(data);

          ctrl.fetchScriptInfo(data.script_path);
          if (!ctrl.scriptExecutionsMap.hasOwnProperty(data.script_path)) {
            ctrl.scriptExecutionsMap[data.script_path] = {};
          }
          ctrl.scriptExecutionsMap[data.script_path][data.execution_id] = data;
          let i = 0;
          ctrl.fetchTestCaseInfo(testCaseExecutionId);
        });
      }
    });
  }

  fetchScriptInfo(scriptPath) {
    this.regressionService.fetchScriptInfoByScriptPath(scriptPath).subscribe(response => {
      this.scriptInfo[scriptPath] = response;
      let i = 0;
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

  _getFlatPath(suiteExecutionId, path, logPrefix) {
    let httpPath = this.logDir + suiteExecutionId;
    let parts = path.split("/");
    let flat = path;
    let numParts = parts.length;
    if (numParts > 2) {
      flat = parts[numParts - 2] + "_" + parts[numParts - 1];
    }
    let s = "";
    if (logPrefix !== "") {
      s = logPrefix + "_"
    }
    return httpPath + "/" + s + flat.replace(/^\//g, '');
  }

  getHtmlLogPath(suiteExecutionId, path, logPrefix) {
    window.open(this._getFlatPath(suiteExecutionId, path, logPrefix) + this.HTML_LOG_EXTENSION);
  }

  getConsoleLogPath(suiteExecutionId, path, logPrefix) {
    window.open(this._getFlatPath(suiteExecutionId, path, logPrefix) + this.CONSOLE_LOG_EXTENSION);
  }

  applyAdditionalAttributes(item) {
    item["showingDetails"] = false;
  }

  showDetailsClick(item) {
    item["showingDetails"] = !item["showingDetails"];
  }

  getSchedulerLog(suiteId) {
    return this.regressionService.getSchedulerLog(suiteId);
  }

  getSchedulerLogDir(suiteId) {
    return this.regressionService.getSchedulerLogDir(suiteId);
  }


  reRunClick(suiteExecutionId, suitePath, resultFilter=null, scriptFilter=null) {
    this.reRunService.submitReRun(suiteExecutionId, suitePath, resultFilter, scriptFilter).subscribe(response => {
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

  clickHistory(scriptPath) {
    let url = "/regression/script_history_page/" + this.scriptInfo[scriptPath].pk;
    window.open(url, '_blank');
  }

  scriptPathToPk(scriptPath) {
    return this.scriptInfo[scriptPath].pk;
  }

  killClick() {
    let suiteId = this.executionId;
    this.regressionService.killSuite(this.executionId).subscribe((result) => {
      this.logger.success(`Killed job: ${result}`);
      window.location.reload()
    }, error => {
      this.logger.error(`Unable kill ${suiteId}`);
    });
  }


}
