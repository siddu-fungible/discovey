import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegressionService} from "../../../regression/regression.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../../services/logger/logger.service";
import {RegisteredAsset} from "../../../regression/definitions";
import {FunTimeSeries, FunTimeSeriesCollection} from "../../definitions";
import {CommonService} from "../../../services/common/common.service";
import {slideInOutAnimation, showAnimation} from "../../../animations/generic-animations";
import {Fs} from "../../../hosts/fs";

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
  clusterIndexes = Array.from(Array(8).keys());
  detectedF1Indexes = new Set();
  showTable: boolean = false;
  showCharts: boolean = false;
  rawTableData: any[] = [];
  rawTableHeaders: any[] = [];

  defaultSelectedPoolName: string = "default_alloc_pool";
  defaultSelectedPoolKey: string = "usage_percent";

  selectedPoolName: string = null;
  selectedPoolKey: string = null;
  updatingCharts: boolean = false;


  fs: Fs = new Fs();

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
      this.parseData();
      return of(true);
    }));

  }

  driver: any = null;

  ngOnInit() {
    // this.selectedPoolName = this.defaultSelectedPoolName;
    // this.selectedPoolKey = this.defaultSelectedPoolKey;
  }

  parseData() {
    let headers = new Set();
    headers.add("Time");
    this.data.forEach(oneRecord => {
      let oneData = [];
      let oneRecordData = oneRecord.data;
      oneData.push(oneRecord.epoch_time);
      Object.keys(oneRecordData).forEach(f1Index => {
        this.detectedF1Indexes.add(f1Index);
        let dataForF1Index = oneRecordData[f1Index];
        headers.add("F1-" + f1Index);
        oneData.push(dataForF1Index);
        this.clusterIndexes.forEach(clusterIndex => {
          let clusterIndexString = `cluster_${clusterIndex}`;
          let poolNames = oneRecordData[f1Index].bm_usage_per_cluster[clusterIndexString];
          Object.keys(poolNames).forEach(poolName => {
            let poolKeys = poolNames[poolName];
            Object.keys(poolKeys).forEach(poolKey => {
              let value = oneRecordData[f1Index].bm_usage_per_cluster[clusterIndexString][poolName][poolKey];
              this.fs.addBamUsage(f1Index, clusterIndex, poolName, poolKey, oneRecord.epoch_time, value);
            });
          });
        });
      });
      this.rawTableData.push(oneData);
    });
    this.rawTableHeaders = Array.from(headers.values());
  }

  prepareStatsData(): void {
    this.fs.f1s.forEach(f1 => {
      let poolNames = Object.keys(this.fs.availablePools);
      poolNames.forEach(poolName => {
        f1[poolName] = {};
        let poolKeys = this.fs.availablePools[poolName];
        poolKeys.forEach(poolKey => {
          f1[poolName][poolKey] = {};
          let title = poolName + "-" + poolKey;
          let funTimeSeriesCollection = new FunTimeSeriesCollection(title, "%", []);
          f1.clusters.forEach(cluster => {
            let name = `PC-${cluster.index}`;
            let oneSeries = new FunTimeSeries(name, {});
            oneSeries.data = cluster.bamUsage[poolName][poolKey];
            funTimeSeriesCollection.collection.push(oneSeries);
          });
          f1[poolName][poolKey]["timeSeries"] = funTimeSeriesCollection;
        });
      });
    });
  }


  ngOnChanges() {
    if (this.scriptExecutionInfo && this.scriptExecutionInfo.suite_execution_id) {
      this.suiteExecutionId = this.scriptExecutionInfo.suite_execution_id;
      this.driver.subscribe(response => {
        this.prepareStatsData();
        this.showCharts = true;
      }, error => {
        this.loggerService.error("Unable to fetch data");
      })
    }
  }

  showTables(): void {
    this.showTable = !this.showTable;
  }

  updatePoolNameAndKey(): void {
    this.updatingCharts = true;
    setTimeout(() => {
      this.defaultSelectedPoolName = this.selectedPoolName;
      this.defaultSelectedPoolKey = this.selectedPoolKey;
      this.updatingCharts = false;
    }, 1);

  }

  updatePoolName(poolName): void {
    this.selectedPoolName = null;
    this.selectedPoolKey = null;
    setTimeout(() => {
      this.selectedPoolName = poolName;
    }, 1);
  }

}
