import {Injectable, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {catchError, switchMap} from 'rxjs/operators';
import {forkJoin, observable, Observable, of, throwError} from "rxjs";
import {CommonService} from "../services/common/common.service";

@Injectable({
  providedIn: 'root'
})
export class RegressionService implements OnInit{
  stateStringMap = { "-200": "UNKNOWN",  // TODO: fetch from the back-end
                   "-100": "ERROR",
                   "-20": "KILLED",
                   "-10": "ABORTED",
                   "10": "COMPLETED",
                   "20": "AUTO_SCHEDULED",
                   "30": "SUBMITTED",
                   "40": "SCHEDULED",
                   "50": "QUEUED",
                   "60": "IN_PROGRESS",
                   "ALL": "ALL"};


  stateMap = {
    "ALL": "ALL",
    "UNKNOWN": "-200",  // TODO: fetch from the back-end
    "ERROR" : -100,
    "KILLED" : -20,
    "ABORTED" : -10,
    "COMPLETED": 10,
    "AUTO_SCHEDULED": 20,
    "SUBMITTED": 30,
    "SCHEDULED": 40,
    "QUEUED": 50,
    "IN_PROGRESS": 60
  };

  logDir: string = null;
  constructor(private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService) { }

  ngOnInit() {

  }



  fetchLogDir() {
    if (!this.logDir) {
      return this.apiService.get("/regression/log_path").pipe(switchMap(response=> {
        return of(response.data);
      }), error => {
        return of("/static/logs/s_");
      });
    } else {
      return of(this.logDir);
    }

  }

  getSchedulerLog(suiteId) {
    return new Observable(observer => {observer.next("ok");}).pipe(switchMap(() => {
      return this.fetchLogDir();
    }), switchMap(logDir => {
        return of(logDir + suiteId + "/scheduler.log.txt");
      }));

  }

  getSchedulerLogDir(suiteId) {
    return new Observable(observer => {observer.next("ok");}).pipe(switchMap(() => {
      return this.fetchLogDir();
    }), switchMap(logDir => {
      return of("/regression/static_serve_log_directory/" + suiteId);
    }));
  }

  convertToLocalTimezone(t) {
    let d = new Date(t.replace(/\s+/g, 'T'));
    let epochValue = d.getTime();
    return new Date(epochValue);
  }

getPrettyLocalizeTime(t) {
  let minutePrefix = '';
  let localTime = this.convertToLocalTimezone(t);
  if (localTime.getMinutes() < 10){
    minutePrefix += '0';
  }
  let s = `${localTime.getMonth() + 1}/${localTime.getDate()} ${localTime.getHours()}:${minutePrefix}${localTime.getMinutes()}`;
  //return this.convertToLocalTimezone(t).toLocaleString().replace(/\..*$/, "");
  return s;
}


  getTestCaseExecution(executionId) {
    return this.apiService.get('/regression/test_case_execution_info/' + executionId).pipe(switchMap((response) => {
      return of(response.data);
    }))
  }

  fetchScriptInfoByScriptPath(scriptPath) {
    let payload = {script_path: scriptPath};
    return this.apiService.post('/regression/script', payload).pipe(switchMap((response) => {
      return of(response.data);
    }));
  }

  fetchTestbeds() {
    return this.apiService.get("/api/v1/regression/test_beds").pipe(switchMap(response => {
      return of(response.data);
    }))
  }

  stateFilterStringToNumber(s) {
    let match = "ALL";
    for (let key in this.stateStringMap) {
      let value = this.stateStringMap[key];
      if (value === s) {
        match = key;
        break;
      }
    }
    return match;
  }

  testBedInProgress(testBedType) {
    /*
    let paramString = `?`;
    let stateStringNumber = this.stateFilterStringToNumber("IN_PROGRESS");
    if (testBedType) {
      paramString += `test_bed_type=${testBedType}&state=${stateStringNumber}`;
    }
    return this.apiService.get("/api/v1/regression/suite_executions" + paramString).pipe(switchMap (response => {
      return of(response.data);
    }))*/

    let url = "/api/v1/regression/test_beds/" + testBedType;
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }))
  }

  getScriptInfo(scriptPk) {
    let url = "/api/v1/regression/script_infos";
    if (scriptPk) {
      url += "/" + scriptPk;
    }
    return this.apiService.get(url).pipe(switchMap (response => {
      return of(response.data);
    }))
  }

  killSuite(suiteId) {
    return this.apiService.get("/regression/kill_job/" + suiteId).pipe(switchMap( (response) => {
      let jobId = parseInt(response.data);
      return of(jobId);
      //window.location.href = "/regression/";
    }));
  }

  disableAutoSchedule(suiteId, disable_schedule) {
    let payload = {"disable_schedule": disable_schedule};
    return this.apiService.put("/api/v1/regression/suite_executions/" + suiteId, payload).pipe(switchMap(response => {
      return of(true);
    }))
  }

  tags(): Observable<string[]> {
    return this.apiService.get('/regression/tags').pipe(switchMap(response => {
      let data = JSON.parse(response.data);
      let i = 1;
      let parsedTags: string [] = [];
      for (let item of data) {
        parsedTags.push(item.fields.tag);
      }
      return of(parsedTags);
    }), catchError(error => {
      return throwError(error);
    }))
  }

  testCaseExecutions(executionId=null, suiteExecutionId=null, scriptPath=null, logPrefix=null) {
    let url = "/api/v1/regression/test_case_executions";
    let queryParams = [];
    if (suiteExecutionId) {
      queryParams.push(["suite_execution_id", suiteExecutionId]);
    }
    if (scriptPath) {
      queryParams.push(["script_path", scriptPath]);
    }
    if (logPrefix !== null) {
      queryParams.push(["log_prefix", logPrefix]);
    }
    let queryParamString = this.commonService.queryParamsToString(queryParams);
    url = `${url}${queryParamString}`;
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);

    }), catchError (error => {
      return throwError(error);
    }))
  }

  testCaseTimeSeries(suiteExecutionId, testCaseExecutionId) {
    let url = `/api/v1/regression/test_case_time_series/${suiteExecutionId}/${testCaseExecutionId}`;
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }), catchError (error => {
      this.loggerService.error("Unable fetch time-series");
      return throwError(error);
    }))
  }

  testCaseTimeSeriesLogs(suiteExecutionId, testCaseExecutionId, checkpointIndex=null) {
    let url = `/api/v1/regression/test_case_time_series/${suiteExecutionId}/${testCaseExecutionId}`;
    url += `?type=log`;
    if (checkpointIndex !== null) {
      url += `&checkpoint_index=${checkpointIndex}`;
    }
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }), catchError (error => {
      this.loggerService.error("Unable fetch time-series logs");
      return throwError(error);
    }))
  }

  testCaseTimeSeriesCheckpoints(suiteExecutionId, testCaseExecutionId) {
    let url = `/api/v1/regression/test_case_time_series/${suiteExecutionId}/${testCaseExecutionId}`;
    url += `?type=checkpoint`;
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }), catchError (error => {
      this.loggerService.error("Unable fetch time-series logs");
      return throwError(error);
    }))
  }

  getRegressionScripts(scriptId=null, scriptPath=null) {
    let url = `/api/v1/regression/scripts`
  }

}
