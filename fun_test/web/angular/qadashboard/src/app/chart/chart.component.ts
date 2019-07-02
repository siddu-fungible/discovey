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
  seriesFilters: any[] = [];
  xAxisLabel: string = null;
  y1AxisLabel: string = null;
  title: string = null;
  chartType: string = null;
  funChartType: string = null;
  xScale: string = null;
  yScale: string = null;

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
    return this.apiService.get("/api/v1/performance/charts/" + this.id).pipe(switchMap(response => {
      this.chartInfo = response.data;
      this.seriesFilters = this.chartInfo.series_filters;
      this.xAxisLabel = this.chartInfo.x_axis_title;
      this.y1AxisLabel = this.chartInfo.y_axis_title;
      this.title = this.chartInfo.title;
      this.chartType = this.chartInfo.chart_type;
      this.funChartType = this.chartInfo.fun_chart_type;
      this.xScale = this.chartInfo.x_scale;
      this.yScale = this.chartInfo.y_scale;
      return of(true);
    }));
  }

  fetchYValues() {
    let payload = {};
    payload["chart_info"] = this.chartInfo;
    return this.apiService.post("/api/v1/performance/data", payload).pipe(switchMap(response => {
      let values = response.data;
      this.initializeY1Values();
      Object.keys(values).forEach((seriesName) => {
        let dataSet = values[seriesName];
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
          let xValue, yValue;
          if (this.xScale.includes('log2')) {
            xValue = Math.log2(Number(sortedValue.name));
          } else if (this.xScale.includes('log10')) {
            xValue = Math.log10(Number(sortedValue.name));
          } else {
            xValue = sortedValue.name;
          }
          if (this.yScale.includes('log2')) {
            yValue = Math.log2(Number(sortedValue.value));
          } else if (this.yScale.includes('log10')) {
            yValue = Math.log10(Number(sortedValue.value));
          } else {
            yValue = sortedValue.value;
          }
          this.xValues.push(xValue);
          for (let y1Value of this.y1Values) {
            if (y1Value.name === seriesName) {
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
    for (let filter of this.seriesFilters) {
      let oneDataSet = {
        name: filter["name"],
        data: [],
        metadata: {}
      };
      this.y1Values.push(oneDataSet);
    }

  }


}
