import { Component, OnInit } from '@angular/core';
import { ApiService}  from "../../services/api/api.service";
import { ActivatedRoute } from "@angular/router";
import {hasOwnProperty} from "tslint/lib/utils";

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

  constructor(private apiService: ApiService, private route: ActivatedRoute) {
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
      //let suiteExecutionJson = JSON.parse(self.suiteExecution);
      let suiteFields = self.suiteExecution.fields;
      let testCaseExecutionIds = JSON.parse(suiteFields.test_case_execution_ids);

      for(let testCaseExecutionId of testCaseExecutionIds) {
        self.apiService.get('/regression/test_case_execution/' + self.executionId + "/" + testCaseExecutionId).subscribe(function (result) {
          //self.testCaseExecutions.push(JSON.parse(result.data)[0]);
          let data = result.data.execution_obj;
          let moreInfo = result.data.more_info;
          data.summary = moreInfo.summary;
          self.testCaseExecutions.push(data);
          if (!ctrl.scriptExecutionsMap.hasOwnProperty(data.script_path)) {
            ctrl.scriptExecutionsMap[data.script_path] = {};
          }
          ctrl.scriptExecutionsMap[data.script_path][data.execution_id] = data;
          let i = 0;
        });
      }
    });
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

  _getFlatPath(path, logPrefix) {
    let httpPath = this.logDir + this.executionId;
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

  getHtmlLogPath(path, logPrefix) {
    window.open(this._getFlatPath(path, logPrefix) + this.HTML_LOG_EXTENSION);
  }

  getConsoleLogPath(path, logPrefix) {
    window.open(this._getFlatPath(path, logPrefix) + this.CONSOLE_LOG_EXTENSION);
  }

  rerunClick(suiteExecutionId, testCaseExecutionId, scriptPath) {
    let payload = {};
    payload["suite_execution_id"] = suiteExecutionId;
    payload["test_case_execution_id"] = testCaseExecutionId;
    payload["script_path"] = scriptPath;
    this.apiService.post("/regression/test_case_re_run", payload).subscribe(function (result) {
      let jobId = parseInt(result.data);
      alert("Rerun Successful");
      window.location.href = "/regression/suite_detail/" + jobId;
    });
  }

}
