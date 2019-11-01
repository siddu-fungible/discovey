import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegressionService} from "../../../regression/regression.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../../services/logger/logger.service";

@Component({
  selector: 'app-bam',
  templateUrl: './bam.component.html',
  styleUrls: ['./bam.component.css']
})
export class BamComponent implements OnInit, OnChanges {
  @Input() scriptExecutionInfo: any = null;
  data: any = null;
  parsedData: any = {};
  suitExecutionId: number = null;
  constructor(private regressionService: RegressionService, private loggerService: LoggerService) {

    this.driver = of(true).pipe(switchMap(response => {
     return this.regressionService.testCaseTimeSeries(this.suitExecutionId, null, null, null, null, 100, 1000);

    })).pipe(switchMap(response => {
      this.data = response;
      this.parseData(this.data);
      return of(true);
    }));

  }
  driver: any = null;
  ngOnInit() {
  }

  parseData(data) {
    this.data.forEach(oneRecord => {
      let oneRecordData = oneRecord.data;
      Object.keys(oneRecordData).forEach(f1Index => {
        let dataForF1Index = oneRecordData[f1Index];
        if (!this.parsedData.hasOwnProperty(f1Index)) {
          this.parsedData[f1Index] = {};
        }
        let poolNames = ["default_alloc_pool"];
        let poolKeys = ["usage_percent"];
        let clusterIndexes = Array.from(Array(8).keys());
        clusterIndexes.forEach(clusterIndex => {
          let clusterIndexString = `cluster_${clusterIndex}`;
          poolNames.forEach(poolName => {
            if (!this.parsedData[f1Index].hasOwnProperty(poolName)) {
              this.parsedData[f1Index][poolName] = {};
            }
            poolKeys.forEach(poolKey => {
              if (!this.parsedData[f1Index][poolName].hasOwnProperty(poolKey)) {
                this.parsedData[f1Index][poolName][poolKey] = [];
              }
              this.parsedData[f1Index][poolName][poolKey].push(oneRecordData[f1Index].bm_usage_per_cluster[clusterIndexString][poolName][poolKey]);
            })
          })
        })




      });
      let j = 0;
    });
  }


  ngOnChanges() {
    if (this.scriptExecutionInfo && this.scriptExecutionInfo.suite_execution_id) {
      this.suitExecutionId = this.scriptExecutionInfo.suite_execution_id;
      this.driver.subscribe(response => {

      }, error => {
        this.loggerService.error("Unable to fetch data");
      })
    }
  }

  refresh() {

  }

}
