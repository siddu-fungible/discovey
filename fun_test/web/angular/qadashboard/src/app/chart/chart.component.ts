import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";

@Component({
  selector: 'chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.css']
})
export class ChartComponent implements OnInit {
  @Input() id: Number = null;
  chartInfo: any = {};
  y1Values: any[] = [];
  xValues: any[] = [];
  showChart: boolean = false;
  dataSets: any[] = [];
  xAxisLabel: string = null;
  y1AxisLabel: string = null;
  title: string = null;
  chartType: string = null;
  funChartType: string = null;

  constructor(private apiService: ApiService, private loggerService: LoggerService) {
  }

  ngOnInit() {
    let self = this;
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(switchMap(response => {
        return self.fetchCharts();
      }),
      switchMap(response => {
        return this.fetchYValues();
      })).subscribe(response => {
    }, error => {
      console.trace();
      this.loggerService.error("Unable to initialize regular chart component");
    });
  }

  fetchCharts() {
    let payload = {};
    payload["chart_id"] = this.id;
    return this.apiService.post("/api/v1/performance/charts", payload).pipe(switchMap(response => {
      this.chartInfo = response.data;
      this.dataSets = this.chartInfo.data_sets;
      this.xAxisLabel = this.chartInfo.xaxis_title;
      this.y1AxisLabel = this.chartInfo.yaxis_title;
      this.title = this.chartInfo.title;
      this.chartType = this.chartInfo.chart_type;
      this.funChartType = this.chartInfo.fun_chart_type;
      return of(true);
    }));
  }

  fetchYValues() {
    let payload = {};
    payload["chart_info"] = this.chartInfo;
    return this.apiService.post("/api/v1/performance/data", payload).pipe(switchMap(response => {
      let values = response.data;
      this.initializeY1Values();
      Object.keys(values).forEach((dataSetName) => {
        let dataSet = values[dataSetName];
        let sortedValues = [];
        dataSet["values"].forEach(function (value, i) {
          let oneValue = {};
          oneValue["name"] = value.x;
          oneValue["value"] = value.y;
          sortedValues.push(oneValue);
        });
        sortedValues.sort((a, b) => (a.name > b.name) ? 1 : ((b.name > a.name) ? -1 : 0));
        this.xValues = [];
        for (let sortedValue of sortedValues) {
          let xValue = Math.log2(Number(sortedValue.name));
          // let xValue = sortedValue.name;
          this.xValues.push(xValue);
          let yValue = Math.log10(Number(sortedValue.value));
          // let yValue = sortedValue.value;
          for (let y1Value of this.y1Values) {
            if (y1Value.name === dataSetName) {
              y1Value.data.push(yValue);
            }
          }
        }
      });
      this.showChart = true;
      return of(true);
    }));
  }

  initializeY1Values() {
    this.y1Values = [];
    for (let dataSet of this.dataSets) {
      let oneDataSet = {
        name: dataSet["name"],
        data: [],
        metadata: {}
      };
      this.y1Values.push(oneDataSet);
    }

  }


}
