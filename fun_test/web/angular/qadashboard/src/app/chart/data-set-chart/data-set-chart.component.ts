import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";

@Component({
  selector: 'data-set-chart',
  templateUrl: './data-set-chart.component.html',
  styleUrls: ['./data-set-chart.component.css']
})
export class DataSetChartComponent implements OnInit {
  @Input() ids: any[] = null;
  @Input() metricId: Number = null;
  companionCharts: any = {};
  REGULAR: string = "Regular";
  y1Values: any[] = [];
  xValues: any[] = [];
  children: any = null;
  showChart: boolean = false;
  dataSets: string[] = [];
  charts: any[] = [];

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
    payload["chart_ids"] = this.ids;
    return this.apiService.post("/api/v1/performance/companion_charts", payload).pipe(switchMap(response => {
      this.companionCharts = response.data;
      // this.dataSets = this.companionCharts[0].data_sets;
      return of(true);
    }));
  }

  fetchYValues() {
    let payload = {};
    payload["companion_charts"] = this.companionCharts;
    payload["metric_id"] = this.metricId;
    return this.apiService.post("/api/v1/performance/get_data_sets_value", payload).pipe(switchMap(response => {
      let values = response.data;

      Object.keys(values).forEach((key) => {
        this.dataSets = this.companionCharts[key]["data_sets"]["names"];
        this.initializeY1Values();
        let sortedValues = [];
        let chartDict = {};
        chartDict["xAxisLabel"] = this.companionCharts[key]["xaxis_title"];
        chartDict["y1AxisLabel"] = this.companionCharts[key]["yaxis_title"];
        chartDict["xValues"] = [];
        chartDict["y1Values"] = [];
        let chartValues = values[key];

        if (chartDict["xAxisLabel"].includes("qDepth")) {
          Object.keys(chartValues).forEach((chartName) => {
            let qd = chartName.split("=");
            let qDepth = Number(qd[qd.length - 1]);
            let value = chartValues[chartName];
            let oneValue = {};
            oneValue["name"] = Math.log2(qDepth);
            oneValue["value"] = value;
            sortedValues.push(oneValue);
          });
        }

        sortedValues.sort((a, b) => (a.name > b.name) ? 1 : ((b.name > a.name) ? -1 : 0));
        for (let sortedValue of sortedValues) {
          chartDict["xValues"].push(sortedValue.name);
          let temp = sortedValue.value;
          for (let oneDataSet of temp) {
            for (let y1Value of this.y1Values) {
              if (y1Value.name === oneDataSet.name) {
                y1Value.data.push(oneDataSet.value);
              }
            }
          }
        }
        chartDict["y1Values"] = this.y1Values;
        this.charts.push(chartDict);
      });

      this.showChart = true;
      return of(true);
    }));
  }

  initializeY1Values() {
    this.y1Values = [];
    for (let dataSet of this.dataSets) {
      let oneDataSet = {
        name: dataSet,
        data: [],
        metadata: {}
      };
      this.y1Values.push(oneDataSet);
    }

  }


}
