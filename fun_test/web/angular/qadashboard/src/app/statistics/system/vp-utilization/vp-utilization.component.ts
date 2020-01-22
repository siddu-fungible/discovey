import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegisteredAsset} from "../../../regression/definitions";
import {RegressionService} from "../../../regression/regression.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {Fs} from "../../../hosts/fs";
import {FunTimeSeries, FunTimeSeriesCollection} from "../../definitions";
import {CommonService} from "../../../services/common/common.service";
import {slideInOutAnimation, showAnimation} from "../../../animations/generic-animations";

@Component({
  selector: 'app-vp-utilization',
  templateUrl: './vp-utilization.component.html',
  styleUrls: ['./vp-utilization.component.css'],
  animations: [slideInOutAnimation, showAnimation]
})
export class VpUtilizationComponent implements OnInit, OnChanges {
  @Input() scriptExecutionInfo: any = null;
  @Input() selectedAsset: RegisteredAsset = null;
  @Input() clusterLevel: boolean = null;
  @Input() title: string = null;
  data: any = null;
  parsedData: any = {};
  driver: any = null;
  suiteExecutionId: number;
  detectedF1Indexes = new Set();
  fs: Fs = new Fs();

  tableHeaders: any = null;
  tableData: any = null;
  showCharts: boolean = false;
  showTable: boolean = false;
  funStatsSeries: FunTimeSeriesCollection[] = [];

  constructor(private regressionService: RegressionService, private loggerService: LoggerService, private commonService: CommonService) {
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
      this.prepareTableHeaders();
      this.parseData(this.data);
      return of(true);
    }));

  }

  prepareTableHeaders(): void {
    this.tableHeaders = [];
    this.tableHeaders.push("Time");
    this.tableHeaders.push("F1-0");
    this.tableHeaders.push("F1-1");
  }

  parseData(data) {
    this.tableData = [];
    this.data.forEach(oneRecord => {
      let oneRecordData = oneRecord.data;
      let record = [];
      record.push(oneRecord.epoch_time);
      Object.keys(oneRecordData).forEach(f1Index => {
        this.detectedF1Indexes.add(f1Index);
        record.push(oneRecordData[f1Index]);
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
      });
      this.tableData.push(record);
    });
  }

  ngOnInit() {
  }

  prepareChartData() {
    this.fs.f1s.forEach(f1 => {
      f1.clusters.forEach(cluster => {
        let index = cluster.index;
        let funTimeSeriesCollection = new FunTimeSeriesCollection("Cluster-" + index, "%", []);
        cluster.cores.forEach(core => {
          core.vps.forEach(vp => {
            let coreIndex = core.index;
            let vpIndex = vp.index;
            let name = `${coreIndex}.${vpIndex}`;
            // console.log(name);
            let oneSeries = new FunTimeSeries(name, {});
            let data = oneSeries.data;
            Object.keys(vp.utilization).forEach(uniqueTimestamp => {
              data[uniqueTimestamp] = vp.utilization[uniqueTimestamp];
            });
            funTimeSeriesCollection.collection.push(oneSeries);
          });
        });
        cluster["timeSeries"] = funTimeSeriesCollection;
      });
    });

    this.fs.f1s.forEach(f1 => {
      let histogramData = [];
      let funTimeSeriesCollection = new FunTimeSeriesCollection("Distribution by number of VPs", "Number", []);
      for (let index = 0; index < 10; index++) {
        let binLow = (index * 10) + 1;
        let binHigh = (index * 10) + 10;
        // console.log(binLow, binHigh);
        let binName = `${binLow}-${binHigh}`;
        let y1Values = new FunTimeSeries(binName, {});
        histogramData.push(y1Values);
      }

      f1.clusters.forEach(cluster => {
        cluster.cores.forEach(core => {
          core.vps.forEach(vp => {
            Object.keys(vp.utilization).forEach(timestamp => {
              let utilization = vp.utilization[timestamp];
              let floorValue = Math.floor(utilization);
              if (histogramData[floorValue].data.hasOwnProperty(timestamp)) {
                histogramData[floorValue].data[timestamp] += 1;
              } else {
                histogramData[floorValue].data[timestamp] = 1;
              }
            });
          });
        })
      });
      funTimeSeriesCollection.collection = histogramData;
      f1["timeSeries"] = funTimeSeriesCollection;
    });
  }

  showTables(): void {
    this.showTable = !this.showTable;
  }

  ngOnChanges() {
    if (this.scriptExecutionInfo && this.scriptExecutionInfo.suite_execution_id) {
      this.suiteExecutionId = this.scriptExecutionInfo.suite_execution_id;
      this.driver.subscribe(response => {
        this.prepareChartData();
        this.showCharts = true;

      }, error => {
        console.log(error.toString());
        this.loggerService.error(`Unable to fetch data`, error);
      })
    }
  }

}
