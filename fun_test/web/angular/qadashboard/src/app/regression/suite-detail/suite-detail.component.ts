import { Component, OnInit } from '@angular/core';
import { ApiService}  from "../../services/api/api.service";
import { ActivatedRoute } from "@angular/router";

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
  suiteExecution: any;
  testCaseExecutions: any;
  attributes: any;

  constructor(private apiService: ApiService, private route: ActivatedRoute) {
  }

  ngOnInit() {
    let self = this;
    this.route.params.subscribe(params => {
      if (params['suiteId']) {
        this.executionId = params['suiteId'];
        this.apiService.get("/regression/suite_execution_attributes/" + this.executionId).subscribe(result => {
          self.attributes = result.data;
        });
      }
    });
    this.logDir = null;
    this.CONSOLE_LOG_EXTENSION = ".logs.txt";  //TIED to scheduler_helper.py  TODO
    this.HTML_LOG_EXTENSION = ".html";         //TIED to scheduler_helper.py  TODO
    if (!this.logDir) {
      this.apiService.get("/regression/log_path1").subscribe(function (result) {
        self.logDir = result.data;
      }, error => {
        self.logDir = "/static/logs/s_";
      });
    }
    this.testCaseExecutions = [];
    this.apiService.get("/regression/suite_execution1/" + this.executionId).subscribe(function (result) {
      self.suiteExecution = result.data; // TODO: validate
      let testCaseExecutionIds = JSON.parse(self.suiteExecution).fields.test_case_execution_ids;
      testCaseExecutionIds = testCaseExecutionIds.substring(1, testCaseExecutionIds.length-1).split(", ");

      for(let testCaseExecutionId of testCaseExecutionIds) {
        self.apiService.get('/regression/test_case_execution1/' + self.executionId + "/" + testCaseExecutionId).subscribe(function (result) {
          self.testCaseExecutions.push(JSON.parse(result.data)[0]);
        });
      }
    });
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

  _getFlatPath(path) {
    let httpPath = this.logDir + this.executionId;
    let parts = path.split("/");
    let flat = path;
    let numParts = parts.length;
    if (numParts > 2) {
      flat = parts[numParts - 2] + "_" + parts[numParts - 1];
    }
    return httpPath + "/" + flat.replace(/^\//g, '');
  }

  getHtmlLogPath(path) {
    return this._getFlatPath(path) + this.HTML_LOG_EXTENSION;
  }

  getConsoleLogPath(path) {
    return this._getFlatPath(path) + this.CONSOLE_LOG_EXTENSION;
  }

  rerunClick(suiteExecutionId, testCaseExecutionId, scriptPath) {
    let payload = {};
    payload["suite_execution_id"] = suiteExecutionId;
    payload["test_case_execution_id"] = testCaseExecutionId;
    payload["script_path"] = scriptPath;
    this.apiService.post("/regression/test_case_re_run1", payload).subscribe(function (result) {
      let jobId = parseInt(result.data);
      window.location.href = "/regression/suite_detail/" + jobId;
    });
  }

}
