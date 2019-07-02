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
  funChartType: string = null;
  xScale: string = null;
  yScale: string = null;

  SCALE_LOG2: string = "log2";
  SCALE_LOG10: string = "log10";

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
        let series = values[seriesName];
        let sortedValues = [];
        series["values"].forEach(function (value, i) {
          let oneValue = {};
          oneValue["x"] = value.x;
          oneValue["y"] = value.y;
          sortedValues.push(oneValue);
        });
        sortedValues.sort((a, b) => (a.x > b.x) ? 1 : ((b.x > a.x) ? -1 : 0));
        this.xValues = [];
        for (let sortedValue of sortedValues) {
          let xValue, yValue;
          xValue = this.setXYValues(this.xScale, sortedValue.x);
          yValue = this.setXYValues(this.yScale, sortedValue.y);
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

  setXYValues(scale, originalValue): number {
    let value;
    if (scale.startsWith(this.SCALE_LOG2)) {
      value = Math.log2(Number(originalValue));
    } else if (scale.startsWith(this.SCALE_LOG10)) {
      value = Math.log10(Number(originalValue));
    } else {
      value = originalValue;
    }
    return value;
  }

  initializeY1Values() {
    this.y1Values = [];
    for (let filter of this.seriesFilters) {
      let oneSeries = {
        name: filter["name"],
        data: [],
        metadata: {}
      };
      this.y1Values.push(oneSeries);
    }

  }


}
