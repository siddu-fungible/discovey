import { Component, OnInit } from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {CommonService} from "../../services/common/common.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ScriptDetailService} from "./script-detail.service";

class TimeSeriesLog {
  date_time: string;
  type: string;
  data: any;
}

class Checkpoint {
  checkpoint: string;
  actual: boolean;
  expected: boolean;
  index: number;
  result: string;
}

@Component({
  selector: 'app-script-detail',
  templateUrl: './script-detail.component.html',
  styleUrls: ['./script-detail.component.css'],
  animations: [
    trigger('show', [
      state('true', style({ opacity: 1, flexGrow: 1, width: "100%"})),
      state('false', style({ opacity: 0, flexGrow: 0, width: 0 })),
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
              private commonService: CommonService,
              private modalService: NgbModal,
              private service: ScriptDetailService
  ) { }
  suiteExecutionId: number = 10000;
  logPrefix: number = null;
  scriptId: number = null;
  scriptPath: string = null;
  testCaseExecutions: any = null;
  currentTestCaseExecution: any = null;
  testLogs = [];
  showTestCasePanel: boolean = true;
  showCheckpointPanel: boolean = false;
  showLogsPanel: boolean = false;
  testCaseIds: number [] = [];
  currentCheckpointIndex: number = null;

  timeSeriesByTestCase: {[testCaseId: number]: {[key: string]: any }} = {};

  ngOnInit() {

    this.driver = of(true).pipe(switchMap(response => {
      return this.regressionService.getScriptInfoById(this.scriptId);
    })).pipe(switchMap(response => {
      return this.service.getContexts(this.suiteExecutionId);
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
      if (params["scriptId"]) {
        this.scriptId = parseInt(params["scriptId"]);
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
    this.regressionService.testCaseTimeSeriesCheckpoints(this.suiteExecutionId, this.testCaseExecutions[testCaseExecutionIndex].execution_id).subscribe(response => {
      this.testCaseExecutions[testCaseExecutionIndex]["checkpoints"] = response;
      let checkpoints = this.testCaseExecutions[testCaseExecutionIndex]["checkpoints"];
      checkpoints.forEach(checkpoint => {
        this.regressionService.testCaseTimeSeriesLogs(this.suiteExecutionId, this.currentTestCaseExecution.execution_id, checkpoint.index).subscribe(response => {
          this.testLogs = response;
          this.currentTestCaseExecution = this.testCaseExecutions[testCaseExecutionIndex];
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
    this.testLogs = null;
    this.currentCheckpointIndex = null;
    this.regressionService.testCaseTimeSeries(this.suiteExecutionId, this.testCaseExecutions[testCaseExecutionIndex].execution_id).subscribe(response => {
      this.currentTestCaseExecution = this.testCaseExecutions[testCaseExecutionIndex];

      let timeSeries = response;
      this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id] = {timeSeries: timeSeries, checkpoints: []};
      timeSeries.forEach(timeSeriesElement => {
        if (timeSeriesElement.type == "checkpoint") { //TODO
          let newCheckpoint = timeSeriesElement.data;
          this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id].checkpoints.push(newCheckpoint);
        }
      });

      this.showCheckpointPanel = true;
    })
  }

  onCheckpointClick(testCaseId, checkpointIndex) {
    this.regressionService.testCaseTimeSeriesLogs(this.suiteExecutionId, this.currentTestCaseExecution.execution_id, checkpointIndex).subscribe(response => {
      this.showTestCasePanel = false;
      this.showLogsPanel = true;
      this.showCheckpointPanel = true;
      let checkpointId = `${testCaseId}_${checkpointIndex}`;
      this.currentCheckpointIndex = checkpointIndex;
      this.commonService.scrollTo(checkpointId);
    }, error => {
      this.loggerService.error("Unable to fetch time-series logs")
    })
  }

  onShowTestCasePanelClick() {
    this.showTestCasePanel = true;
    this.showCheckpointPanel = true;
    this.showLogsPanel = false;
    this.currentCheckpointIndex = null;
  }

  onContextOptionsClick(content) {
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((suiteExecution) => {

    }, (reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    });
  }

}
