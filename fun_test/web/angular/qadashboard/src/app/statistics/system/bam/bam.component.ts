import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegressionService} from "../../../regression/regression.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../../services/logger/logger.service";
import {RegisteredAsset} from "../../../regression/definitions";
import {FunTimeSeries, FunTimeSeriesCollection} from "../../definitions";
import {CommonService} from "../../../services/common/common.service";
import {slideInOutAnimation, showAnimation} from "../../../animations/generic-animations";

@Component({
  selector: 'app-bam',
  templateUrl: './bam.component.html',
  styleUrls: ['./bam.component.css'],
  animations: [slideInOutAnimation, showAnimation]
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
  clusterIndexes = Array.from(Array(9).keys());
  detectedF1Indexes = new Set();
  showTable: boolean = false;
  showCharts: boolean = false;
  rawTableData: any[] = [];
  rawTableHeaders: any[] = [];

  constructor(private regressionService: RegressionService, private loggerService: LoggerService, private commonService: CommonService) {
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
    let headers = new Set();
    headers.add("Time");
    this.data.forEach(oneRecord => {
      let oneData = [];
      let oneRecordData = oneRecord.data;
      let dateTime = this.commonService.getShortTimeFromEpoch(Number(oneRecord.epoch_time) * 1000);
      oneData.push(dateTime);
      Object.keys(oneRecordData).forEach(f1Index => {
        this.detectedF1Indexes.add(f1Index);
        let dataForF1Index = oneRecordData[f1Index];
        headers.add("F1-" + f1Index);
        oneData.push(dataForF1Index);
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
            let title = poolName + "-" + poolKey;
            let funTimeSeriesCollection = new FunTimeSeriesCollection(title, "%", []);
            if (!this.parsedData[f1Index][poolName].hasOwnProperty(poolKey)) {
              this.parsedData[f1Index][poolName][poolKey] = [];  // store array of cluster data here
              this.clusterIndexes.forEach(clusterIndex => {
                let name = `PC-${clusterIndex}`;
                let oneSeries = new FunTimeSeries(name, {});
                this.parsedData[f1Index][poolName][poolKey].push(oneSeries);
              });
            }
            this.clusterIndexes.forEach(clusterIndex => {
              let clusterIndexString = `cluster_${clusterIndex}`;
              this.parsedData[f1Index][poolName][poolKey][clusterIndex].data[Number(oneRecord.epoch_time) * 1000] = oneRecordData[f1Index].bm_usage_per_cluster[clusterIndexString][poolName][poolKey];
            });
            funTimeSeriesCollection.collection = this.parsedData[f1Index][poolName][poolKey];
            this.parsedData[f1Index][poolName][poolKey]["funTimeSeries"] = funTimeSeriesCollection;
          });
        });
      });
      this.rawTableData.push(oneData);
    });
    this.rawTableHeaders = Array.from(headers.values())
  }


  ngOnChanges() {
    if (this.scriptExecutionInfo && this.scriptExecutionInfo.suite_execution_id) {
      this.suiteExecutionId = this.scriptExecutionInfo.suite_execution_id;
      this.driver.subscribe(response => {
        this.showCharts = true;
      }, error => {
        this.loggerService.error("Unable to fetch data");
      })
    }
  }

  showTables(): void {
    this.showTable = !this.showTable;
  }

}
