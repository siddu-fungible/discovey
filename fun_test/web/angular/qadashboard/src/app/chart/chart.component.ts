import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {OnChange} from "ngx-bootstrap";

@Component({
  selector: 'chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.css']
})
export class ChartComponent implements OnInit {
  @Input() id: Number = null;
  companionChartInfo: any = {};
  REGULAR: string = "Regular";
  y1Values: any[] = [];
  xValues: any[] = [];
  children: any = null;
  showChart: boolean = false;
  dataSets: any[] = [];
  charts: any = {};
  xAxisLabel: string = null;
  y1AxisLabel: string = null;
  title: string = null;

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
        return self.fetchCompanionCharts();
      }),
      switchMap(response => {
        return this.fetchYValues();
      })).subscribe(response => {
    }, error => {
      console.trace();
      this.loggerService.error("Unable to initialize regular chart component");
    });
  }

  fetchCompanionCharts() {
    let payload = {};
    payload["chart_id"] = this.id;
    return this.apiService.post("/api/v1/performance/companion_chart_info", payload).pipe(switchMap(response => {
      this.companionChartInfo = response.data;
      this.dataSets = this.companionChartInfo.data_sets;
      this.xAxisLabel = this.companionChartInfo.xaxis_title;
      this.y1AxisLabel = this.companionChartInfo.yaxis_title;
      this.title = this.companionChartInfo.title;
      return of(true);
    }));
  }

  fetchYValues() {
    let payload = {};
    payload["companion_chart_info"] = this.companionChartInfo;
    return this.apiService.post("/api/v1/performance/get_data_sets_value", payload).pipe(switchMap(response => {
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
