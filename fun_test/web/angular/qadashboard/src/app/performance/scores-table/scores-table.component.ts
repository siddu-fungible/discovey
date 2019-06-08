import {Component, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {ApiService} from "../../services/api/api.service";

@Component({
  selector: 'app-scores-table',
  templateUrl: './scores-table.component.html',
  styleUrls: ['./scores-table.component.css']
})
export class ScoresTableComponent implements OnInit {
  chartName: string = null;
  modelName: string = null;
  rows: any = {};
  metricId: number = null;

  constructor(private route: ActivatedRoute, private apiService: ApiService) {
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['metricId']) {
        this.metricId = params['metricId'];
      }
    });
    if (this.metricId) {
      let self = this;
      let payload = {};
      payload["metric_id"] = this.metricId;
      this.apiService.post("/metrics/chart_info", payload).subscribe((chartInfo) => {
        if (chartInfo.data) {
          self.chartName = chartInfo.data.chart_name;
          self.modelName = chartInfo.data.metric_model_name;
          let rows = {};
          this.apiService.post("/metrics/scores", payload).subscribe((response) => {
            if (response.data.length !== 0) {
              let keyList = Object.keys(response.data.scores);
              keyList.sort();
              keyList.forEach((dateTime) => {
                let d = new Date(Number(dateTime) * 1000).toISOString();
                let score = response.data.scores[dateTime].score;
                let copiedScore = response.data.scores[dateTime].copied_score;
                let copiedDisposition = response.data.scores[dateTime].copied_score_disposition;
                rows[d] = {score: score, copiedScore: copiedScore, copiedDisposition: copiedDisposition};
              });
            }
            self.rows = rows;
          });
        }

      });
    }
  }

}
