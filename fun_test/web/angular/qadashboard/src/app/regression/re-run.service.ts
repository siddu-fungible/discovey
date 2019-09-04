import {Injectable} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {catchError, switchMap} from 'rxjs/operators';
import {forkJoin, Observable, of} from "rxjs";


@Injectable({
  providedIn: 'root'
})
export class ReRunService {
  suiteContents = null;
  info = {};
  suitePath = null;
  reRunVersion = null;
  archivedJobSpec = null;

  constructor(private apiService: ApiService, private loggerService: LoggerService) {
  }

  submitReRun(suiteExecution, resultFilter=null, scriptFilter=null, reUseBuildImage=null) {
    let payload = {suite_execution_id: suiteExecution.execution_id, suite_id: suiteExecution.suite_id, result_filter: resultFilter, script_filter: scriptFilter, re_use_build_image: reUseBuildImage};
    return this.apiService.post('/api/v1/regression/re_run_job', payload);
  }


  fetchArchivedJob(suiteExecutionId) {
    return this.apiService.get("/regression/job_spec/" + suiteExecutionId).pipe(switchMap(response => {
      this.archivedJobSpec = response.data;
      return of(null);
    }));
  }

  fetchSuiteContents(suiteExecutionId, suitePath) {
    if (!suitePath.endsWith(".py")) {
      let payload = {suite_path: suitePath};
      return this.apiService.post("/regression/suites", payload).pipe(switchMap((response) => {
        if (!suitePath.endsWith(".json")) {
          suitePath = suitePath + ".json";
        }
        this.suiteContents = response.data[suitePath];
        return of(null);
      }));
    } else {
      this.suiteContents = [{path: this.archivedJobSpec.script_path}];  // Not a suite, but an individual script
      return of(null);
    }

  }

  fetchSuiteExecutionApplyFilter(suiteExecutionId, resultFilter=null, scriptFilter=null) {
    return this.apiService.get("/regression/suite_execution/" + suiteExecutionId).pipe(switchMap(result => {
      this.reRunVersion = result.data.fields.version;
      let testCaseExecutionIds = JSON.parse(result.data.fields.test_case_execution_ids);
      //let numTestCases = testCaseExecutionIds.length;
      return forkJoin(...testCaseExecutionIds.map((testCaseExecutionId) => {
          return this.apiService.get("/regression/test_case_execution/" + suiteExecutionId + "/" + testCaseExecutionId).pipe(switchMap(response => {
            let executionObj = response.data.execution_obj;
            let suiteLineIndex = executionObj.log_prefix;

            let selected: boolean = true;
            if (resultFilter) {
              let testResult = executionObj.result;
              if (resultFilter.indexOf(testResult) === -1) {
                selected = false;
              }
            }
            if (scriptFilter) {
              if (executionObj.script_path !== scriptFilter) {
                selected = false;
              }
            }
            if (selected) {
              if (!this.info.hasOwnProperty(suiteLineIndex)) {
                this.info[suiteLineIndex] = {re_run_info: {}};
              }
              this.info[suiteLineIndex].re_run_info[executionObj.test_case_id] = {test_case_execution_id: executionObj.execution_id};
            }
            return of(null);
          }))
        })
      )
    }));
  }


  prepareSuite() {
    return new Observable((observer) => {
      let scriptItems = [];
      if (this.suiteContents.length > 0) {
        if (this.suiteContents[0].hasOwnProperty('info')) {
          scriptItems.push(this.suiteContents[0]);
        }
      }

      let suiteIndices = Object.keys(this.info);
      suiteIndices.forEach(suiteIndex => {
        let thisSuiteIndex = parseInt(suiteIndex); // log_prefix/suite index is 1 based
        let scriptItem = this.suiteContents[thisSuiteIndex];
        scriptItem["re_run_info"] = this.info[suiteIndex].re_run_info;
        console.log(scriptItem);
        scriptItems.push(scriptItem);
      });
      observer.next(scriptItems);
    })

  }

  submitJob(scriptItems, suiteExecutionId, reUseBuildImage=null) {

    let payload = {dynamic_suite_spec: scriptItems,
      version: this.reRunVersion,
      original_suite_execution_id: suiteExecutionId,
      emails: this.archivedJobSpec["emails"],
      submitter_email: this.archivedJobSpec["submitter_email"],
      environment: this.archivedJobSpec["environment"]};

    if (!reUseBuildImage) {
      let environment = this.archivedJobSpec.environment;
      if (environment.hasOwnProperty("with_jenkins_build") && environment.with_jenkins_build) {

        if (reUseBuildImage === false && environment.hasOwnProperty("tftp_image_path")) {
          delete environment["tftp_image_path"];
        }
      }
    }

    if (this.archivedJobSpec.hasOwnProperty("inputs")) {
      try {
        payload["job_inputs"] = JSON.parse(this.archivedJobSpec["inputs"]);
      } catch (e) {
        payload["job_inputs"] =this.archivedJobSpec["inputs"];
      }

    }

    if (this.archivedJobSpec.hasOwnProperty('test_bed_type')) {
      payload["test_bed_type"] = this.archivedJobSpec["test_bed_type"];
    }
    return this.apiService.post("/regression/submit_job", payload)
  }

  getOriginalSuiteReRunInfo(suiteExecutionId) {
    let payload = {original_suite_execution_id: suiteExecutionId};
    return this.apiService.post('/regression/re_run_info', payload).pipe(switchMap(response => {
      let result = {};

      result["numTotal"] = 0;
      result["numActive"] = 0;
      result["numCompleted"] = 0;
      if (response.data) {
        let reRunInfo = response.data;
        for (let index = 0; index < reRunInfo.length; index++) {
          result["numTotal"] += 1;
          let reRunState = reRunInfo[index].re_run.attributes.result;

          if (reRunState >= 30) { // TODO
            result["numActive"] += 1;
          } else {
            result["numCompleted"] += 1;
          }// JobStatusType.SUBMITTED // TODO

        }
        result["reRunInfo"] = reRunInfo;
      }
      return of(result);
    }))
  }

  getReRunSuiteInfo(suiteExecutionId) {
    let payload = {re_run_suite_execution_id: suiteExecutionId};
    return this.apiService.post('/regression/re_run_info', payload).pipe(switchMap(response => {
      let result = {};
      result["reRunInfo"] = response.data;
      return of(result);
    }));
  }

}
