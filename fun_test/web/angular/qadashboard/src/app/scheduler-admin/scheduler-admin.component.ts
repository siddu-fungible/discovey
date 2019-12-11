import { Component, OnInit } from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'app-scheduler-admin',
  templateUrl: './scheduler-admin.component.html',
  styleUrls: ['./scheduler-admin.component.css']
})
export class SchedulerAdminComponent implements OnInit {
  gitLogs = null;
  gitPullLog = null;
  info: any = null;
  directiveTypes: any = null;
  stateTypes: any = null;
  gitPullStatus = null;
  constructor(private apiService: ApiService,
              private loggerService: LoggerService) { }

  ngOnInit() {
    this.fetchGitLogs();
    this.fetchInfo();
    new Observable(observer => {
      observer.next(true);
      return () => {}
    }).pipe(switchMap((response) => {
      return this.fetchDirectiveTypes();
    })).pipe(switchMap((response) => {
      return this.fetchStateTypes();
    })).pipe(switchMap((response) => {
      return this.fetchInfo();
    })).subscribe(() => {
    }, error => {
      this.loggerService.error("Unable to fetch state info");
    })
  }

  gitPull() {
    let payload = {command: "pull"};
    this.gitPullStatus = "Performing git pull";
    this.apiService.post('/regression/git', payload).subscribe(response => {
        this.gitPullLog = response.data.pull;
        this.fetchGitLogs();
        this.gitPullStatus = null;

      }
    )
  }
  fetchGitLogs() {
    let payload = {command: "logs"};
    this.apiService.post('/regression/git', payload).subscribe(response => {
        this.gitLogs = response.data.logs;
      }
    )
  }

  fetchInfo() {
    return this.apiService.get('/api/v1/scheduler/info').pipe(switchMap(response => {
      this.info = response.data;
      return of(true);
    }))
  }

  fetchDirectiveTypes() {
    return this.apiService.get('/api/v1/scheduler/directive_types').pipe(switchMap(response => {
      this.directiveTypes = response.data;
      return of(true);
    }))
  }

  fetchStateTypes() {
    return this.apiService.get('/api/v1/scheduler/state_types').pipe(switchMap(response => {
      this.stateTypes = response.data;
      return of(true);
    }))
  }

  pause() {
    let payload = {directive: this.directiveTypes.PAUSE_QUEUE_WORKER};
    this.apiService.post('/api/v1/scheduler/directive', payload).subscribe(response => {

    });
  }

  unpause() {
    let payload = {directive: this.directiveTypes.UNPAUSE_QUEUE_WORKER};
    this.apiService.post('/api/v1/scheduler/directive', payload).subscribe(response => {

    });
  }

}
