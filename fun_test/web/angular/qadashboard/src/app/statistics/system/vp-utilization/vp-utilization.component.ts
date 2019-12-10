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
  data: any = null;
  parsedData: any = {};
  driver: any = null;
  suiteExecutionId: number;
  detectedF1Indexes = new Set();
  fs: Fs = new Fs();
  maxChartsPerRow: number = 3;

  xSeries: any = null;
  TIMEZONE: string = "America/Los_Angeles";
  tableHeaders: any = null;
  tableData: any = null;
  showCharts: boolean = false;
  funStatsSeries: FunTimeSeriesCollection[] = [];
  y1Values: FunTimeSeries[] = [];

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
    this.tableHeaders.push("Datetime");
    this.tableHeaders.push("Value");
  }

  parseData(data) {
    this.tableData = {};
    this.tableData[0] = [];
    this.tableData[1] = [];
    this.data.forEach(oneRecord => {
      let dateTime = this.commonService.getShortDateTimeFromEpoch(oneRecord.epoch_time * 1000, this.TIMEZONE);
      let oneRecordData = oneRecord.data;
      Object.keys(oneRecordData).forEach(f1Index => {
        this.detectedF1Indexes.add(f1Index);
        let record = [];
        record.push(dateTime);
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
        this.tableData[f1Index].push(record);

      });
    });
  }

  ngOnInit() {
  }

  prepareChartData() {

    // find unique timestamps
    let uniqueTimestampsSet = new Set();
    this.fs.f1s.forEach(f1 => {
      f1.clusters.forEach(cluster => {
        cluster.cores.forEach(core => {
          core.vps.forEach(vp => {
            Object.keys(vp.utilization).map(timestamp => uniqueTimestampsSet.add(timestamp));

          })
        })
      })
    });
    let uniqueTimestamps = Array.from(uniqueTimestampsSet.values()).sort();
    this.fs.f1s.forEach(f1 => {
      f1.clusters.forEach(cluster => {
        cluster["debug_vp_util"] = {series: []};
        cluster["tableHeaders"] = ["Datetime"];
        cluster["tableData"] = [];
        let dataSet = {};
        uniqueTimestamps.forEach(uniqueTimestamp => {
          let dateTime = this.commonService.getShortDateTimeFromEpoch(uniqueTimestamp * 1000, this.TIMEZONE);
          dataSet[dateTime] = [];
        });
        let index = cluster.index;
        let funTimeSeriesCollection = new FunTimeSeriesCollection("Cluster-" + index, "Sample", "%", null,[]);
        cluster.cores.forEach(core => {
          let numVps = 0;
          let sumOfUtilizations = 0;
          core.vps.forEach(vp => {
            let coreIndex = core.index;
            let vpIndex = vp.index;
            let name = `${coreIndex}.${vpIndex}`;
            // console.log(name);
            let oneSeries = new FunTimeSeries(name, []);
            cluster["tableHeaders"].push(name);
            let data = oneSeries.data;
            uniqueTimestamps.forEach(uniqueTimestamp => {
               let dateTime = this.commonService.getShortDateTimeFromEpoch(uniqueTimestamp * 1000, this.TIMEZONE);
              if (vp.utilization.hasOwnProperty(uniqueTimestamp)) {
                data.push(vp.utilization[uniqueTimestamp]);
                // cluster["tableData"].push([dateTime, vp.utilization[uniqueTimestamp]]);
                numVps += 1;
                sumOfUtilizations += vp.utilization[uniqueTimestamp] * 100;
                dataSet[dateTime].push(vp.utilization[uniqueTimestamp]);
              } else {
                data.push(-1);
                // cluster["tableData"].push([dateTime, -1]);
                dataSet[dateTime].push(-1);
              }
            });
            cluster["debug_vp_util"].series.push(oneSeries);
          })
        });
        funTimeSeriesCollection.y1Values = cluster["debug_vp_util"].series;
        cluster["funTimeSeries"] = funTimeSeriesCollection;
        Object.keys(dataSet).forEach(date => {
          let temp = [];
          temp.push(date);
          let result = temp.concat(dataSet[date]);
          cluster["tableData"].push(result);
        });
      });
    });


    this.xSeries = uniqueTimestamps;


    this.fs.f1s.forEach(f1 => {
      let histogramData = [];
      let funTimeSeriesCollection = new FunTimeSeriesCollection("VP utilization distribution (Range of percentages)", "Sample", "Number" +
        " of VPs", null,[]);
      for (let index = 0; index < 10; index++) {
        let binLow = (index * 10) + 1;
        let binHigh = (index * 10) + 10;
        // console.log(binLow, binHigh);
        let binName = `${binLow}-${binHigh}`;
        let series = {name: binName, data:[]};
        let y1Values = new FunTimeSeries(binName, []);
        histogramData.push(y1Values);
      }
      let currentTimestampIndex = 0;
      uniqueTimestamps.forEach(timestamp => {

        histogramData.forEach(histogramElement => {
          histogramElement.data.push(0);
        });
        f1.clusters.forEach(cluster => {
          cluster.cores.forEach(core => {
            core.vps.forEach(vp => {
              if (vp.utilization.hasOwnProperty(timestamp)) {
                let utilization = vp.utilization[timestamp];
                let floorValue = Math.floor(utilization);
                histogramData[floorValue].data[currentTimestampIndex] += 1;
              }
            })
          })
        });
        currentTimestampIndex += 1;

      });

      f1["histogram"] = histogramData;
      funTimeSeriesCollection.y1Values = histogramData;
      f1["funTimeSeries"] = funTimeSeriesCollection;
    });
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
