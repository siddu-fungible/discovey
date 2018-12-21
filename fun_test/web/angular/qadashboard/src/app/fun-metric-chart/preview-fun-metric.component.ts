import { Component } from '@angular/core';
import { FunMetricChartComponent } from "./fun-metric-chart.component";

@Component({
  selector: 'preview-fun-metric',
  templateUrl: './fun-metric-chart.component.html',
  styleUrls: ['./fun-metric-chart.component.css']
})
export class PreviewFunMetricComponent extends FunMetricChartComponent {
  getPreviewDataSets() {
    return this.previewDataSets;
  }
}
