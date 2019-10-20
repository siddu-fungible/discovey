import {Component, OnInit } from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {CommonService} from "../../services/common/common.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ScriptDetailService, ContextInfo} from "./script-detail.service";
import {Pipe, PipeTransform } from '@angular/core';
import {ElementRef, ViewChild} from '@angular/core';
import * as d3 from 'd3';

class DataModel {
  letter: string;
  frequency: number;
}



class TimeSeriesLog {
  epoch_time: number;
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

@Pipe({name: 'selected'})
export class selected implements PipeTransform {
  transform(value: ContextInfo []): ContextInfo [] {
    return value.filter(element => element.selected);
  }
}


@Component({
  selector: 'app-script-detail',
  templateUrl: './script-detail.component.html',
  styleUrls: ['./script-detail.component.css'],
  animations: [trigger('show', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(300)
      ]),
      transition(':leave', [
        animate(1, style({ opacity: 1.0 }))
      ]),
      state('*', style({ opacity: 1.0 })),
    ])]
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
  availableContexts: ContextInfo [] = [];


  timeSeriesByTestCase: {[testCaseId: number]: {[key: string]: any }} = {};

  ngOnInit() {

    this.driver = of(true).pipe(switchMap(response => {
      return this.regressionService.getScriptInfoById(this.scriptId);
    })).pipe(switchMap(response => {
      this.scriptPath = response.script_path;
      return this.service.getContexts(this.suiteExecutionId, this.scriptId);
    })).pipe(switchMap(response => {
      this.availableContexts = response;
      this.availableContexts.map(availableContext => {
        availableContext["selected"] = false;
      });
      let defaultContext = new ContextInfo();
      defaultContext.context_id = 0;
      defaultContext.description = "Default";
      defaultContext.selected = true;

      this.availableContexts.unshift(defaultContext);
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
      this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id] = {timeSeries: timeSeries,
        checkpoints: [], minimum_epoch: 0, maximum_epoch: 0};
      let thisEntry = this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id];
      timeSeries.forEach(timeSeriesElement => {
        if (timeSeriesElement.epoch_time < thisEntry.minimum_epoch) {
          thisEntry.minimum_epoch = timeSeriesElement.epoch_time;
        }
        if (timeSeriesElement.epoch_time > thisEntry.maximum_epoch) {
          thisEntry.maximum_epoch = timeSeriesElement.epoch_time;
        }
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

  onTimeLineChanged(valueChanged) {
    console.log(valueChanged);
  }
}
