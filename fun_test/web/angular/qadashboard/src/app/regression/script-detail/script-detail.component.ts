import {Component, OnInit } from '@angular/core';
import {RegressionService} from "../regression.service";
import {forkJoin, Observable, of, throwError} from "rxjs";
import {catchError, last, switchMap, windowWhen} from "rxjs/operators";
import {LoggerService} from "../../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {CommonService} from "../../services/common/common.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ScriptDetailService, ContextInfo, ScriptRunTime} from "./script-detail.service";
import {Pipe, PipeTransform } from '@angular/core';

class DataModel {
  letter: string;
  frequency: number;
}



class TimeSeriesLog {
  epoch_time: number;
  relative_epoch_time: number;
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
  currentTestCaseExecutionIndex: number = null;
  testLogs = [];
  showTestCasePanel: boolean = true;
  showCheckpointPanel: boolean = false;
  showLogsPanel: boolean = false;
  testCaseIds: number [] = [];
  currentCheckpointIndex: number = null;
  availableContexts: ContextInfo [] = [];
  selectedContexts: ContextInfo [] = [];
  minRelativeTime: number = 0;
  maxRelativeTime: number = 1;
  scriptRunTime: ScriptRunTime = null;
  timeFilterMin: number = 0;
  status: string = null;
  logPanelHeight: any = "500px";
  DEFAULT_LOOKBACK_LOGS: number = 100;
  numLookbackLogs: number = 100;

  //timeSeriesByTestCase: {[testCaseId: number]: {[key: string]: any }} = {};

  ngOnInit() {

    this.driver = of(true).pipe(switchMap(response => {
      return this.service.getScriptRunTime(this.suiteExecutionId, this.scriptId);
    })).pipe(switchMap(response => {
      this.scriptRunTime = response;
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
      this.testCaseExecutions.forEach(testCaseExecution => {
        testCaseExecution["relative_started_epoch_time"] = testCaseExecution["started_epoch_time"] - this.scriptRunTime.started_epoch_time;

      });
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

  parseCheckpoints(checkpoints) {
    let lastCheckpoint = null;
    let currentCheckpoint = null;
    checkpoints.forEach(checkpoint => {
      checkpoint["previous_checkpoint"] = null;
      currentCheckpoint = checkpoint;
      checkpoint["relative_epoch_time"] = checkpoint.epoch_time - this.scriptRunTime.started_epoch_time;
      if (lastCheckpoint) {
        lastCheckpoint["relative_end_epoch_time"] = checkpoint.relative_epoch_time;
        checkpoint["previous_checkpoint"] = lastCheckpoint;
      }

      lastCheckpoint = checkpoint;
    });
    lastCheckpoint["relative_end_epoch_time"] = currentCheckpoint["relative_epoch_time"] + 100; //TODO: Derive this from script run time


  }


  fetchCheckpoints(testCaseExecution, suiteExecutionId) {

    let testCaseId = testCaseExecution.test_case_id;
    /*
    let timeSeriesEntry = this.timeSeriesByTestCase[testCaseId];
    if (!timeSeriesEntry) {
      this.timeSeriesByTestCase[testCaseId] = {checkpoints: null, minimum_epoch: 0, maximum_epoch: 0};
      timeSeriesEntry = this.timeSeriesByTestCase[testCaseId];
    }*/

    if (testCaseExecution.hasOwnProperty("checkpoints") && (testCaseExecution.checkpoints) && (testCaseExecution.checkpoints.length > 0)) {
      return of(true)
    } else {
      return this.regressionService.testCaseTimeSeriesCheckpoints(suiteExecutionId, testCaseExecution.execution_id).pipe(switchMap(response => {
        if (!testCaseExecution.hasOwnProperty("checkpoints")) {
          testCaseExecution["checkpoints"] = response;
          testCaseExecution["minimum_epoch"] = 0;
          testCaseExecution["maximum_epoch"] = 0;
        } else {
          testCaseExecution["checkpoints"] = response;
        }
        this.parseCheckpoints(testCaseExecution.checkpoints);
        return of(true);
      }))
    }
  }

  onTestCaseIdClick(testCaseExecutionIndex) {
    this.testLogs = null;
    this.currentCheckpointIndex = null;
    this.currentTestCaseExecution = this.testCaseExecutions[testCaseExecutionIndex];
    this.status = "Fetching checkpoints";
    this.fetchCheckpoints(this.currentTestCaseExecution, this.suiteExecutionId).subscribe(response => {
      this.status = null;
      this.showCheckpointPanel = true;

    }, error => {
      this.loggerService.error("Unable to fetch checkpoints");
      this.status = null;

    });

    /*this.regressionService.testCaseTimeSeriesCheckpoints(this.suiteExecutionId, )*/


    /*
    this.testLogs = null;
    this.currentCheckpointIndex = null;
    this.status = "Fetching test-case executions";
    this.regressionService.testCaseTimeSeries(this.suiteExecutionId, this.testCaseExecutions[testCaseExecutionIndex].execution_id).subscribe(response => {
      this.currentTestCaseExecution = this.testCaseExecutions[testCaseExecutionIndex];
      this.currentTestCaseExecutionIndex = testCaseExecutionIndex;

      let timeSeries = response;
      this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id] = {timeSeries: timeSeries,
        checkpoints: [], minimum_epoch: 0, maximum_epoch: 0};
      let thisEntry = this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id];
      timeSeries.forEach(timeSeriesElement => {

        timeSeriesElement.relative_epoch_time = timeSeriesElement.epoch_time - this.scriptRunTime.started_epoch_time;
        if (timeSeriesElement.relative_epoch_time < thisEntry.minimum_epoch) {
          thisEntry.minimum_epoch = timeSeriesElement.relative_epoch_time;
        }
        if (timeSeriesElement.relative_epoch_time > thisEntry.maximum_epoch) {
          thisEntry.maximum_epoch = timeSeriesElement.relative_epoch_time;
        }

        if (timeSeriesElement.relative_epoch_time > this.maxRelativeTime) {
          this.maxRelativeTime = timeSeriesElement.relative_epoch_time;
        }

        if (timeSeriesElement.type == "checkpoint") { //TODO
          let newCheckpoint = timeSeriesElement.data;
          this.timeSeriesByTestCase[this.currentTestCaseExecution.test_case_id].checkpoints.push(newCheckpoint);
        }
      });

      this.showCheckpointPanel = true;
      this.status = null;
    })*/
  }
  onCheckpointClick2(testCaseExecution, checkpointIndex, contextId?: 0) {

  }

  onCheckpointClick(testCaseExecution, checkpointIndex, contextId?: 0) {
    //this.status = "Fetching checkpoint data";
    this.numLookbackLogs = this.DEFAULT_LOOKBACK_LOGS;
    this.currentCheckpointIndex = checkpointIndex;
    this.showTestCasePanel = false;
    this.showLogsPanel = true;
    this.showCheckpointPanel = true;
    /*
    let checkpointId = `${testCaseId}_${checkpointIndex}_${contextId}`;

    */

    let selectedCheckpoint = testCaseExecution.checkpoints[checkpointIndex];
    let checkpointsInConsideration = [selectedCheckpoint];
    if (selectedCheckpoint.previous_checkpoint) {
      checkpointsInConsideration.unshift(selectedCheckpoint.previous_checkpoint);
    }
    console.log(checkpointsInConsideration);
    /*let minEpoch = checkpointsInConsideration.reduce((min, p) => p.relative_epoch_time < min ? p.relative_epoch_time: min , checkpointsInConsideration[0].relative_epoch_time);
    let maxEpoch = checkpointsInConsideration.reduce((max, p) => p.relative_end_epoch_time > max ? p.relative_end_epoch_time: max, checkpointsInConsideration[0].relative_end_epoch_time);

    console.log(minEpoch, maxEpoch);
    let trueRange = [this.scriptRunTime.started_epoch_time + minEpoch, this.scriptRunTime.started_epoch_time + maxEpoch];
    console.log(trueRange);
    console.log(checkpointsInConsideration);*/


    /*let checkpointIndexesToFetch: number [] = checkpointsInConsideration.map(e => e.data.index);
    let minCheckpointIndex = Math.min(...checkpointIndexesToFetch);
    let maxCheckpointIndex: number = Math.max(...checkpointIndexesToFetch);*/

    let checkpointIndexesToFetch = Array.from(Array(checkpointIndex + 1).keys());
    //checkpointIndexesToFetch = checkpointIndexesToFetch.filter(checkpointIndex => !testCaseExecution.checkpoints[checkpointIndex].hasOwnProperty("timeSeries"));
    let checkpointId = `${testCaseExecution.test_case_id}_${checkpointIndex}_${contextId}`;

    this.fetchLogsForCheckpoints(this.currentTestCaseExecution, checkpointIndexesToFetch, checkpointIndex).subscribe(response => {
      this.showLogsPanel = true;
      this.status = null;
      setTimeout(() => {
        this.commonService.scrollTo(checkpointId);
      }, 10);


    }, error => {
      this.loggerService.error("Unable to fetch logs for checkpoints");
      this.status = null;
    })


  }


  fetchLogsForCheckpoints(testCaseExecution, checkpointIndexesToFetch, checkpointIndexClicked): Observable<any> {
    checkpointIndexesToFetch = checkpointIndexesToFetch.filter(checkpointIndex => {
      return !testCaseExecution.checkpoints[checkpointIndex].hasOwnProperty("timeSeries") && ((checkpointIndexClicked === checkpointIndex || ((checkpointIndexClicked - checkpointIndex) === 1)));
    });

    if (checkpointIndexesToFetch.length > 0) {
      let minCheckpointIndex = checkpointIndexesToFetch[0];
      if (checkpointIndexesToFetch.length > 1) {
        minCheckpointIndex = checkpointIndexesToFetch[checkpointIndexesToFetch.length - 2];
      }
      let maxCheckpointIndex = checkpointIndexesToFetch[checkpointIndexesToFetch.length - 1];
      this.status = "Fetching logs";
      return this.regressionService.testCaseTimeSeries(this.suiteExecutionId, testCaseExecution.execution_id, null, minCheckpointIndex, maxCheckpointIndex).pipe(switchMap(response => {
        this.status = "Parsing logs";
        setTimeout(() => {

          response.forEach(timeSeriesElement => {
            let checkpointIndex = timeSeriesElement.data.checkpoint_index;
            if (!testCaseExecution.checkpoints[checkpointIndex].hasOwnProperty("timeSeries")) {
              testCaseExecution.checkpoints[checkpointIndex]["timeSeries"] = [];
            }
            timeSeriesElement["relative_epoch_time"] = timeSeriesElement.epoch_time - this.scriptRunTime.started_epoch_time;
            testCaseExecution.checkpoints[checkpointIndex].timeSeries.push(timeSeriesElement);
          });
          this.status = null;
          this.setMinimumTime();
        }, 1);

        return of(true);
      }), catchError (error => {
        this.loggerService.error("Unable fetch checkpoint logs");
        return throwError(error);
      }))
    } else {
      return of(true);
    }

  }

  setMinimumTime() {
    let maxEntries = this.numLookbackLogs;
    let count = 0;
    let checkpointIndexesToCheck = [this.currentCheckpointIndex];
    if ((this.currentTestCaseExecution.checkpoints.length - 2) >= this.currentCheckpointIndex) {
      checkpointIndexesToCheck.unshift(this.currentCheckpointIndex - 1);
    }
    checkpointIndexesToCheck = checkpointIndexesToCheck.reverse();

    checkpointIndexesToCheck.forEach(checkpointIndexToCheck => {
      let timeSeries = this.currentTestCaseExecution.checkpoints[checkpointIndexToCheck].timeSeries;
      let i = timeSeries.length - 1;
      if (count < maxEntries) {
        for (; i >= 0; i--, count++) {

          if (count > maxEntries) {
            break;
          }
          this.timeFilterMin = timeSeries[i].relative_epoch_time;
        }
      }
    })
  }

  fetchLogsForCheckpoint(testCaseExecution, checkpointIndex) {
    return this.regressionService.testCaseTimeSeries(this.suiteExecutionId, testCaseExecution.execution_id, checkpointIndex).pipe(switchMap(response => {
      let testCaseId = testCaseExecution.test_case_id;
      testCaseExecution.checkpoints[checkpointIndex]["timeSeries"] = response;

      testCaseExecution.checkpoints[checkpointIndex]["timeSeries"].forEach(seriesElement => {
        seriesElement["relative_epoch_time"] = seriesElement.epoch_time - this.scriptRunTime.started_epoch_time;
      });
      return of(true);
    }, error => {

    }))
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
    this.selectedContexts = this.availableContexts.filter(availableContext => availableContext.selected);

  }

  findMatchingTestCase(time): number {
    let testCaseIndex = 0;
    let found = false;
    for (let index = 0; index < this.testCaseExecutions.length; index++) {
      if (this.testCaseExecutions[index].result === "NOT_RUN") {
        continue;
      }
      if (this.testCaseExecutions[index].relative_started_epoch_time <= time) {
      } else {
        break;
      }
      testCaseIndex = index;

    }
    console.log(`TC: ${testCaseIndex}`);
    return testCaseIndex;
  }

  onTimeLineChanged(valueChanged) {
    console.log(valueChanged);
    this.timeFilterMin = valueChanged;
    let testCaseIndex = this.findMatchingTestCase(this.timeFilterMin);
    if (this.currentTestCaseExecutionIndex !== testCaseIndex) {
      this.onTestCaseIdClick(testCaseIndex)
    }
  }

  testClick() {
    //console.log(this.selectedContexts);
    let element = document.getElementById("logs-panel");
    console.log(element.getBoundingClientRect().top);
    console.log(window.top);
    console.log(window.innerHeight);
    this.logPanelHeight = window.innerHeight - element.getBoundingClientRect().top - 70;
    console.log(this.logPanelHeight);
  }
}
