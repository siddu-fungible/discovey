import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegressionService} from "../../../regression/regression.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../../services/logger/logger.service";
import {RegisteredAsset} from "../../../regression/definitions";

@Component({
  selector: 'app-bam',
  templateUrl: './bam.component.html',
  styleUrls: ['./bam.component.css']
})
export class BamComponent implements OnInit, OnChanges {
  @Input() scriptExecutionInfo: any = null;
  @Input() selectedAsset: RegisteredAsset = null;
  @Input() title: string = null;
  data: any = null;
  parsedData: any = {};
  suiteExecutionId: number = null;
  bmUsagePerClusterPoolNames: string [] = ["default_alloc_pool", "nu_erp_fcp_pool"];
  bmUsagePerClusterPoolKeys: string [] = ["usage_percent"];
  clusterIndexes = Array.from(Array(8).keys());
  detectedF1Indexes = new Set();

  constructor(private regressionService: RegressionService, private loggerService: LoggerService) {
    this.driver = of(true).pipe(switchMap(response => {
     return this.regressionService.testCaseTimeSeries(this.suiteExecutionId,
       null,
       null,
       null,
       null,
       100,
       1000, this.selectedAsset.asset_id);

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
        this.detectedF1Indexes.add(f1Index);
        let dataForF1Index = oneRecordData[f1Index];
        if (!this.parsedData.hasOwnProperty(f1Index)) {
          this.parsedData[f1Index] = {};
        }
        let poolNames = this.bmUsagePerClusterPoolNames;
        let poolKeys = this.bmUsagePerClusterPoolKeys;


          poolNames.forEach(poolName => {
            if (!this.parsedData[f1Index].hasOwnProperty(poolName)) {
              this.parsedData[f1Index][poolName] = {};
            }
            poolKeys.forEach(poolKey => {
              if (!this.parsedData[f1Index][poolName].hasOwnProperty(poolKey)) {
                this.parsedData[f1Index][poolName][poolKey] = [];  // store array of cluster data here
                this.clusterIndexes.forEach(clusterIndex => {
                  this.parsedData[f1Index][poolName][poolKey].push({name: `PC-${clusterIndex}`, data: []});
                })
              }
              this.clusterIndexes.forEach(clusterIndex => {
                let clusterIndexString = `cluster_${clusterIndex}`;
                let element =
                this.parsedData[f1Index][poolName][poolKey][clusterIndex].data.push(oneRecordData[f1Index].bm_usage_per_cluster[clusterIndexString][poolName][poolKey]);
              });
            })
          })


      });

      let j = 0;
    });
  }


  ngOnChanges() {
    if (this.scriptExecutionInfo && this.scriptExecutionInfo.suite_execution_id) {
      this.suiteExecutionId = this.scriptExecutionInfo.suite_execution_id;
      this.driver.subscribe(response => {

      }, error => {
        this.loggerService.error("Unable to fetch data");
      })
    }
  }

  refresh() {

  }

}
