import { Component, OnInit } from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {animate, state, style, transition, trigger} from "@angular/animations";

class TimeSeriesLog {
  date_time: string;
  type: string;
  data: any;
}

@Component({
  selector: 'app-script-detail',
  templateUrl: './script-detail.component.html',
  styleUrls: ['./script-detail.component.css'],
  animations: [
    trigger('show', [
      state('true', style({ opacity: 1, flexGrow: 1})),
      state('false', style({ opacity: 0, flexGrow: 0 })),
      transition('false => true', animate('300ms')),
      transition('true => false', animate('300ms')),

    ])
  ]
})
export class ScriptDetailComponent implements OnInit {
  driver: Observable<any> = null;
  constructor(private regressionService: RegressionService,
              private loggerService: LoggerService,
              private route: ActivatedRoute,
  ) { }
  suiteExecutionId: number = 10000;
  logPrefix: number = null;
  scriptPk: number = null;
  scriptPath: string = null;
  testCaseExecutions: any = null;
  currentTestCaseExecution: any = null;
  testLogs = [];
  showTestCasePanel: boolean = true;
  showLogsPanel: boolean = false;
  testCaseIds: number [] = [];

  timeSeriesByTestCase: {[testCaseId: number]: TimeSeriesLog} = {};

  ngOnInit() {

    this.driver = of(true).pipe(switchMap(response => {
      return this.regressionService.getScriptInfo(this.scriptPk);
    })).pipe(switchMap(response => {
      this.scriptPath = response.script_path;
      return this.regressionService.testCaseExecutions(null, this.suiteExecutionId, this.scriptPath, this.logPrefix);
    })).pipe(switchMap(response => {
      this.testCaseExecutions = response;
      return of(true);
    }));

    this.route.params.subscribe(params => {
      if (params['suiteExecutionId']) {
        this.suiteExecutionId = parseInt(params['suiteExecutionId']);

      }
      if (params['logPrefix']) {
        this.logPrefix = params['logPrefix'];
      }
      if (params["scriptPk"]) {
        this.scriptPk = parseInt(params["scriptPk"]);
      }
      this.refreshAll();

    });



  }

  refreshAll() {
    this.driver.subscribe(response => {

    }, error => {
      this.loggerService.error("Unable to initialize script-detail component");
    })

  }

  onTestCaseIdClick1(testCaseExecutionIndex, testCaseExecutionId) {
    this.testLogs = null;
    console.log(testCaseExecutionIndex);
    this.currentTestCaseExecution = this.testCaseExecutions[testCaseExecutionIndex];
    this.regressionService.testCaseTimeSeriesCheckpoints(this.suiteExecutionId, this.testCaseExecutions[testCaseExecutionIndex].execution_id).subscribe(response => {
      this.testCaseExecutions[testCaseExecutionIndex]["checkpoints"] = response;
      let checkpoints = this.testCaseExecutions[testCaseExecutionIndex]["checkpoints"];
      checkpoints.forEach(checkpoint => {
        this.regressionService.testCaseTimeSeriesLogs(this.suiteExecutionId, this.currentTestCaseExecution.execution_id, checkpoint.index).subscribe(response => {
          this.testLogs = response;
        }, error => {
          this.loggerService.error("Unable to fetch time-series logs")
        });
      });
      console.log(response);
    }, error => {
      this.loggerService.error("Unable to fetch time-series checkpoints");
    })
  }

  onTestCaseIdClick(testCaseExecutionIndex) {
    this.currentTestCaseExecution = this.testCaseExecutions[testCaseExecutionIndex];
    this.testLogs = null;

    this.regressionService.testCaseTimeSeries(this.suiteExecutionId, this.testCaseExecutions[testCaseExecutionIndex].execution_id).subscribe(response => {
      let timeSeries = response;
      this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id] = timeSeries;
      this.showTestCasePanel = true;
    })
  }

  onCheckpointClick(checkpointIndex) {
    this.regressionService.testCaseTimeSeriesLogs(this.suiteExecutionId, this.currentTestCaseExecution.execution_id, checkpointIndex).subscribe(response => {
      this.showTestCasePanel = false;
      this.showLogsPanel = true;
    }, error => {
      this.loggerService.error("Unable to fetch time-series logs")
    })
  }

  onShowTestCasePanelClick() {
    this.showTestCasePanel = true;
    this.showLogsPanel = false;
  }

}
