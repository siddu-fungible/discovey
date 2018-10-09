import { Component, OnInit } from '@angular/core';
import { FunMetricChartComponent } from "./fun-metric-chart.component";
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'preview-fun-metric',
  templateUrl: './fun-metric-chart.component.html',
  styleUrls: ['./fun-metric-chart.component.css']
})
export class PreviewFunMetricComponent extends FunMetricChartComponent {
  constructor(public apiService: ApiService, public loggerService: LoggerService, public route: ActivatedRoute){
    super(apiService, loggerService, route);
  }
   // populates chartInfo and fetches metrics data
  fetchInfo(): void {
    let payload = {};
    payload["metric_model_name"] = this.modelName;
    payload["chart_name"] = this.chartName;
    this.apiService.post("/metrics/chart_info", payload).subscribe((response) => {
      this.chartInfo = response.data;
      if (this.chartInfo !== null) {
        if (!this.previewDataSets) {
          this.previewDataSets = this.chartInfo.data_sets;
        }
        this.currentDescription = this.chartInfo.description;
        this.inner.currentDescription = this.currentDescription;
        this.negativeGradient = !this.chartInfo.positive;
        this.inner.negativeGradient = this.negativeGradient;
        this.leaf = this.chartInfo.leaf;
        this.inner.leaf = this.leaf;
        this.status = "idle";
      }
      setTimeout(() => {
        this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, this.previewDataSets);
      }, this.waitTime);
    }, error => {
      this.loggerService.error("fun_metric_chart: chart_info");
    });
  }

}
