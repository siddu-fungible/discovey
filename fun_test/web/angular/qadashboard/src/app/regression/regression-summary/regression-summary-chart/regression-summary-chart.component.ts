import {Component, EventEmitter, Input, OnChanges, OnInit, Output} from '@angular/core';

@Component({
  selector: 'app-regression-summary-chart',
  templateUrl: './regression-summary-chart.component.html',
  styleUrls: ['./regression-summary-chart.component.css']
})
export class RegressionSummaryChartComponent implements OnInit, OnChanges {
  @Input() versionList = [];
  @Input() timeBucketList = [];
  @Input() filterEntry: any = null;
  @Input() public pointClickCallback: Function;
  @Input() title: string = null;
  @Input() mode: string = "version";
  @Output() pointInfo: EventEmitter<any> = new EventEmitter();

  y1Values: any = [];
  x1Values: any = [];

  constructor() { }

  ngOnInit() {
    this.initializeY1Values();
    this.parseTestCaseInfo();
  }

  ngOnChanges() {
    this.initializeY1Values();
    this.parseTestCaseInfo();
  }

  initializeY1Values() {

    this.y1Values = [{
        name: 'Passed',
        data: [],
        color: 'green',
        metadata: {index: this.filterEntry.index, mode: this.mode},
        mode: this.mode
    }
    ,  {
        name: 'Failed',
        data: [],
        color: 'red',
        metadata: {index: this.filterEntry.index, mode: this.mode},
        mode: this.mode

    }, {
        name: 'Not-run',
        data: [],
        color: 'grey',
        metadata: {index: this.filterEntry.index, mode: this.mode},
        mode: this.mode

    }];
  }

  showPointDetails(pointInfo): void {
    this.pointInfo.emit(pointInfo);
  }

  populateResults(infoSection) {
    if (infoSection) {
      let numPassed = infoSection.numPassed;
      let numFailed = infoSection.numFailed;
      let numNotRun = infoSection.numNotRun;
      this.y1Values[0].data.push(numPassed);
      this.y1Values[1].data.push(numFailed);
      this.y1Values[2].data.push(numNotRun);
    }
  }

  prepareValues() {
    this.y1Values = [];
    this.initializeY1Values();
    let infoSection = null;
    if (this.mode === "version") {
      this.versionList.forEach(version => {
      if (!Number.isNaN(version)) {
          infoSection = this.filterEntry.bySoftwareVersion[version];
          this.populateResults(infoSection);
        }
      });
      this.x1Values = this.versionList;
    } else {
      this.timeBucketList.forEach(timeBucket => {
        infoSection = this.filterEntry.byDateTime[timeBucket];
        this.populateResults(infoSection);
      });
      this.x1Values = this.timeBucketList;
    }

  }

  parseTestCaseInfo() {
    this.prepareValues();
  }

}
