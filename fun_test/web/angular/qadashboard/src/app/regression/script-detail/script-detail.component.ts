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
import {StatisticsService, StatisticsCategory, StatisticsSubCategory} from "../../statistics/statistics.service";

class DataModel {
  letter: string;
  frequency: number;
}


class TimeSeriesLog {
  epoch_time: number;
  relative_epoch_time: number;
  type: number;
  data: any;
}

class Checkpoint {
  checkpoint: string;
  actual: boolean;
  expected: boolean;
  index: number;
  result: string;
}


class ArtifactElement {
  asset_id: string;
  asset_type: string;
  category: string;
  sub_category: string;
  description: string;
  filename: string;
  link: string;
}

class Artifact {
  epoch_time: number;
  te: number;
  type: number;
  data: ArtifactElement;

}

class TableData {
  headers: string [];
  rows: any [];

}

class TestCaseTableElement {
  table_data: TableData;
  table_name: string;
  panel_header: string;
}

class TestCaseTable {
  data: TestCaseTableElement;
  epoch_time: number;
  te: number;
  type: number;
}

class ArtifactTree {
  root = {};

  addArtifact(artifact: Artifact, staticLogDir: string) {
    if (!this.root.hasOwnProperty(artifact.data.asset_type)) {
      this.root[artifact.data.asset_type] = {};
    }
    let assetTypeEntry = this.root[artifact.data.asset_type];
    if (!assetTypeEntry.hasOwnProperty(artifact.data.asset_id)) {
      assetTypeEntry[artifact.data.asset_id] = {};
    }
    let assetIdEntry = assetTypeEntry[artifact.data.asset_id];
    if (!assetIdEntry.hasOwnProperty(artifact.data.category)) {
      assetIdEntry[artifact.data.category] = [];
    }
    let categoryEntry = assetIdEntry[artifact.data.category];
    let parts = artifact.data.filename.split("/");
    if (parts.length > 0) {
      artifact.data.link = `${staticLogDir}/${parts[parts.length - 1]}`;

    }
    categoryEntry.push(artifact);
  }

  clear() {
    this.root = {};
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
  values = [{data: [{y: 45}, {y: 51}, {y: 73}]}];
  series = [1, 2, 3];
  artifacts: Artifact [] = null;

  constructor(private regressionService: RegressionService,
              private loggerService: LoggerService,
              private route: ActivatedRoute,
              private commonService: CommonService,
              private modalService: NgbModal,
              private service: ScriptDetailService
  ) {
    this.selectedStatistics = [];
    let sc = new StatisticsCategory();
    sc.display_name = "System";
    sc.name = "system";
    let ssc = new StatisticsSubCategory();
    ssc.display_name = "BAM";
    ssc.name = "bam";
    //this.selectedStatistics.push({statisticsCategory: sc, statisticsSubCategory: ssc});
  }
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
  logsAreTruncated: boolean = false;
  viewingCharts: boolean = false;
  statisticsCategories: any [] = [
    {name: "system", display_name: "System", "sub_categories": [{name: "bam", display_name: "BAM"}]}
  ];
  selectedStatisticsCategory = null;
  selectedStatisticsSubCategory = null;
  selectedStatistics: any [] = null;
  scriptExecutionInfo = {};
  checkpointPanelStatus: string = null;
  showFailedCheckpoints: boolean = false;
  showFailedTestCases: boolean = false;

  showingArtifactPanel: boolean = false;
  artifactTree: ArtifactTree = new ArtifactTree();
  showingTablesPanel: boolean = false;
  testCaseTablePanels: {[panelHeader: string]: any} = {};

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
      this.updateScriptExecutionInfo();
      return this.regressionService.testCaseTables(this.suiteExecutionId);
    })).pipe(switchMap(response => {
      this._parseTestCaseTables(response);
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

  _parseTestCaseTables(response) {
    response.forEach(element => {
      if (!this.testCaseTablePanels.hasOwnProperty(element.data.panel_header)) {
        this.testCaseTablePanels[element.data.panel_header] = [];
      }
      this.testCaseTablePanels[element.data.panel_header].push(element);
    });
    return
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

  openConsoleLogClick() {
    this.regressionService.getConsoleLogPath(this.suiteExecutionId, this.scriptPath, this.logPrefix);
  }

  fetchCheckpoints(testCaseExecution, suiteExecutionId) {

    let testCaseId = testCaseExecution.test_case_id;

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
    this.showLogsPanel = false;
    this.currentTestCaseExecution = this.testCaseExecutions[testCaseExecutionIndex];
    this.updateScriptExecutionInfo();

    this.checkpointPanelStatus = "Fetching checkpoints";
    this.fetchCheckpoints(this.currentTestCaseExecution, this.suiteExecutionId).subscribe(response => {
      this.checkpointPanelStatus = null;
      this.showCheckpointPanel = true;

    }, error => {
      this.loggerService.error("Unable to fetch checkpoints");
      this.status = null;

    });

  }
  onCheckpointClick2(testCaseExecution, checkpointIndex, contextId?: 0) {

  }

  showContext(contextId) {
    for (let index = 0; index < this.availableContexts.length; index++) {
      if (contextId === this.availableContexts[index].context_id) {
        this.availableContexts[index].selected = true;
        break;
      }
    }
  }

  _restoreCheckpointDefaults() {
    this.numLookbackLogs = this.DEFAULT_LOOKBACK_LOGS;
    this.timeFilterMin = 0;
  }

  onCheckpointClick(testCaseExecution, checkpointIndex, contextId?: 0) {
    this.showContext(contextId);
    this._restoreCheckpointDefaults();
    this.currentCheckpointIndex = checkpointIndex;
    this.updateScriptExecutionInfo();

    //this.showTestCasePanel = false;
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


    let checkpointIndexesToFetch = Array.from(Array(checkpointIndex + 1).keys());
    //checkpointIndexesToFetch = checkpointIndexesToFetch.filter(checkpointIndex => !testCaseExecution.checkpoints[checkpointIndex].hasOwnProperty("timeSeries"));
    let checkpointId = `${testCaseExecution.test_case_id}_${checkpointIndex}_${contextId}`;

    this.fetchLogsForCheckpoints(this.currentTestCaseExecution, checkpointIndexesToFetch, checkpointIndex).subscribe(response => {
      this.showLogsPanel = true;
      this.logsAreTruncated = this.setMinimumTime();
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

        response.forEach(timeSeriesElement => {
          let checkpointIndex = timeSeriesElement.data.checkpoint_index;
          if (!testCaseExecution.checkpoints[checkpointIndex].hasOwnProperty("timeSeries")) {
            testCaseExecution.checkpoints[checkpointIndex]["timeSeries"] = [];
          }
          timeSeriesElement["relative_epoch_time"] = timeSeriesElement.epoch_time - this.scriptRunTime.started_epoch_time;
          testCaseExecution.checkpoints[checkpointIndex].timeSeries.push(timeSeriesElement);
        });
        this.status = null;

        console.log("Done parsing logs");


        return of(true);
      }), catchError (error => {
        this.loggerService.error("Unable fetch checkpoint logs");
        return throwError(error);
      }))
    } else {
      return of(true);
    }

  }

  setMinimumTime(): boolean {
    let maxEntries = this.numLookbackLogs;
    let count = 0;
    let checkpointIndexesToCheck = [this.currentCheckpointIndex];
    if (this.currentTestCaseExecution.checkpoints.length > 0 && ((this.currentCheckpointIndex - 1) > 0 )) {
      checkpointIndexesToCheck.push(this.currentCheckpointIndex - 1);
    }

    let maxReached = false;
    for (let checkpointIteratorIndex = 0; checkpointIteratorIndex < checkpointIndexesToCheck.length; checkpointIteratorIndex++) {
      if (maxReached) {
        break;
      }
      let timeSeries = this.currentTestCaseExecution.checkpoints[checkpointIndexesToCheck[checkpointIteratorIndex]].timeSeries;
      let i = timeSeries.length - 1;
      if (count < maxEntries) {
        for (; i >= 0; i--, count++) {

          if (count > maxEntries) {
            maxReached = true;
            console.log(`Max reached: ${maxReached} time: ${this.timeFilterMin}`);
            break;
          }
          this.timeFilterMin = timeSeries[i].relative_epoch_time;
        }
      }

    }
    return maxReached;
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

  showPreviousLogsClick() {
    this.numLookbackLogs += 100;
    this.logsAreTruncated = this.setMinimumTime();
  }

  viewChartsClick(content) {
    this.selectedStatisticsCategory = null;
    this.selectedStatisticsSubCategory = null;
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((suiteExecution) => {
    }, (reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    });
  }

  addStatisticsCategory() {
    if (!this.selectedStatisticsCategory) {
      return this.loggerService.error("Statistics category not selected");
    }

    if (!this.selectedStatisticsSubCategory) {
      return this.loggerService.error("Statistics sub-category not selected");
    }

    if (!this.selectedStatistics) {
      this.selectedStatistics = [];
    }

    this.selectedStatistics.push({statisticsCategory: this.selectedStatisticsCategory,
      statisticsSubCategory: this.selectedStatisticsSubCategory});
    this.selectedStatisticsCategory = null;
    this.selectedStatisticsSubCategory = null;
    this.selectedStatistics = [...this.selectedStatistics];
  }

  deleteSelectedStatisticClick(index) {
    this.selectedStatistics.splice(index, 1);
    this.selectedStatistics = [...this.selectedStatistics];
  }

  updateScriptExecutionInfo() {
    this.scriptExecutionInfo["suite_execution_id"] = this.suiteExecutionId;
    this.scriptExecutionInfo["current_test_case_execution"] = this.currentTestCaseExecution;
    this.scriptExecutionInfo["current_checkpoint_index"] = this.currentCheckpointIndex;
    this.scriptExecutionInfo = {...this.scriptExecutionInfo};
  }

  openArtifactsPanelClick() {
    this.showingArtifactPanel = !this.showingArtifactPanel;
    this.regressionService.artifacts(this.suiteExecutionId).subscribe(response => {
      this.artifacts = response;
      this._parseArtifacts();

    }, error => {
      this.loggerService.error("Unable to open artifacts panel");
    });
  }

  _parseArtifacts() {
    this.artifactTree.clear();
    this.artifacts.forEach(artifact => {
      this.artifactTree.addArtifact(artifact, `/static/logs/s_${this.suiteExecutionId}`);
    })
  }

  openTestCaseTablesPanelClick() {
    this.showingTablesPanel = !this.showingTablesPanel;
  }

}
