import {Injectable, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {catchError, switchMap} from 'rxjs/operators';
import {forkJoin, observable, Observable, of} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class RegressionService implements OnInit{
  logDir: string = null;
  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

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
    return this.convertToLocalTimezone(t).toLocaleString().replace(/\..*$/, "");
  }

  getTestCaseExecution(executionId) {
    return this.apiService.get('/regression/test_case_execution_info/' + executionId).pipe(switchMap((response) => {
      return of(response.data);
    }))
  }

}
