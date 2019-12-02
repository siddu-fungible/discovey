import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegisteredAsset} from "../../../regression/definitions";
import {RegressionService} from "../../../regression/regression.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {Fs} from "../../../hosts/fs";

@Component({
  selector: 'app-vp-utilization',
  templateUrl: './vp-utilization.component.html',
  styleUrls: ['./vp-utilization.component.css']
})
export class VpUtilizationComponent implements OnInit, OnChanges {
  @Input() scriptExecutionInfo: any = null;
  @Input() selectedAsset: RegisteredAsset = null;
  data: any = null;
  parsedData: any = {};
  driver: any = null;
  suiteExecutionId: number;
  detectedF1Indexes = new Set();
  fs: Fs = new Fs();

  constructor(private regressionService: RegressionService, private loggerService: LoggerService) {
    this.driver = of(true).pipe(switchMap(response => {
     return this.regressionService.testCaseTimeSeries(this.suiteExecutionId,
       null,
       null,
       null,
       null,
       100,
       1050, this.selectedAsset.asset_id);

    })).pipe(switchMap(response => {
      this.data = response;
      this.parseData(this.data);
      return of(true);
    }));

  }

  parseData(data) {
    this.data.forEach(oneRecord => {
      let oneRecordData = oneRecord.data;
      Object.keys(oneRecordData).forEach(f1Index => {
        this.detectedF1Indexes.add(f1Index);
        /*
        let dataForF1Index = oneRecordData[f1Index];
        if (!this.parsedData.hasOwnProperty(f1Index)) {
          this.parsedData[f1Index] = {};
        }*/
        Object.keys(oneRecordData[f1Index]).forEach(clusterKey => {
          let regex = /CCV(\d+)_(\d+)_(\d+)/;
          let match = regex.exec(clusterKey);
          if (match) {
            let clusterIndex = parseInt(match[1]);
            let coreIndex = parseInt(match[2]);
            let vpIndex = parseInt(match[3]);
            //console.log("Done");
            this.fs.addDebugVpUtil(parseInt(f1Index), clusterIndex, coreIndex, vpIndex, oneRecord.epoch_time, oneRecordData[f1Index][clusterKey]);
          }

        });
        let j = 0;

      });
    });
  }

  ngOnInit() {
  }

  ngOnChanges() {
    if (this.scriptExecutionInfo && this.scriptExecutionInfo.suite_execution_id) {
      this.suiteExecutionId = this.scriptExecutionInfo.suite_execution_id;
      this.driver.subscribe(response => {

      }, error => {
        console.log(error.toString());
        this.loggerService.error(`Unable to fetch data`, error);
      })
    }
  }

}
