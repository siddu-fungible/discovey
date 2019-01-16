import {Component, EventEmitter, Input, OnChanges, OnInit, Output} from '@angular/core';

@Component({
  selector: 'app-regression-summary-chart',
  templateUrl: './regression-summary-chart.component.html',
  styleUrls: ['./regression-summary-chart.component.css']
})
export class RegressionSummaryChartComponent implements OnInit, OnChanges {
  @Input() testCaseExecutions: any = null;
  @Input() versionSet: any = null;
  @Input() suiteExectionVersionMap: any = null;
  @Input() public pointClickCallback: Function;
  @Input() metadata: any = null;
  @Input() title: string = null;
  @Output() pointInfo: EventEmitter<any> = new EventEmitter();

  availableVersions = new Set();
  availableVersionList = [];
  bySoftwareVersion: any = {};
  y1Values: any = [];

  constructor() { }

  ngOnInit() {
    this.initializeY1Values();
    this.parseTestCaseInfo();
    let i = 0;
  }

  ngOnChanges() {
    this.initializeY1Values();
    this.parseTestCaseInfo();
  }

  initializeY1Values() {
    let moduleName = "m";
    this.y1Values = [{
        name: 'Passed',
        data: [],
        color: 'green',
        metadata: this.metadata
    }
    ,  {
        name: 'Failed',
        data: [],
        color: 'red',
        metadata: this.metadata

    }, {
        name: 'Not-run',
        data: [],
        color: 'grey',
        metadata: this.metadata

    }];
  }

  showPointDetails(pointInfo): void {
    this.pointInfo.emit(pointInfo);
  }

  prepareY1Values() {
    this.availableVersions.forEach(version => {
      if (!Number.isNaN(version)) {
        let infoSection = this.bySoftwareVersion[version];
        let numPassed = infoSection.numPassed;
        let numFailed = infoSection.numFailed;
        let numNotRun = infoSection.numNotRun;
        this.y1Values[0].data.push(numPassed);
        this.y1Values[1].data.push(numFailed);
        this.y1Values[2].data.push(numNotRun);
      }


    });
  }

  getPlaceHolder() {
    return {numPassed: 0, numFailed: 0, numNotRun: 0};
  }

  parseTestCaseInfo() {
    if (this.testCaseExecutions) {
      this.testCaseExecutions.forEach((testCaseExecution) => {
        let actualVersion = this.suiteExectionVersionMap[testCaseExecution.suite_execution_id];
        this.availableVersions.add(actualVersion);
        if (!this.bySoftwareVersion.hasOwnProperty(actualVersion)) {
          this.bySoftwareVersion[actualVersion] = this.getPlaceHolder();
        }
        let infoSection = this.bySoftwareVersion[actualVersion];
        if (testCaseExecution.result === "PASSED") {
          infoSection.numPassed += 1;
        } else if (testCaseExecution.result === "FAILED") {
          infoSection.numFailed += 1;
        } else {
          infoSection.numNotRun += 1;
        }

      });

    }


    this.prepareY1Values();
    this.availableVersionList = Array.from(this.availableVersions.values());
    let i = 0;

  }

  getArrayFromSet(s) {
    return Array.from(s.values());
  }

}
