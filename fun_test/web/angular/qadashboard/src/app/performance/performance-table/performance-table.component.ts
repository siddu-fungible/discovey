import {Component, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {ApiService} from "../../services/api/api.service";

@Component({
  selector: 'app-data-table',
  templateUrl: './performance-table.component.html',
  styleUrls: ['./performance-table.component.css']
})
export class PerformanceTableComponent implements OnInit {
  chartName: string = null;
  modelName: string = null;
  metricId: number = null;
  inputs: any[] = [];
  outputList: any[] = [];
  tableInfo: any = null;
  headers: string[] = null;
  data: any = {};
  showingTable: boolean = false;

  constructor(private route: ActivatedRoute, private apiService: ApiService) {
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['metricId']) {
        this.metricId = params['metricId'];
      }
    });
    //this.data has values for the fun table
    this.data["rows"] = [];
    this.data["headers"] = [];
    this.data["all"] = true;
    this.data["pageSize"] = 10;
    this.data["currentPageIndex"] = 1;
    this.data["totalLength"] = this.data["rows"].length;
    if (this.metricId) {
      let self = this;
      let payload = {};
      payload["metric_id"] = this.metricId;
      this.apiService.post("/metrics/chart_info", payload).subscribe((chartInfo) => {
        if (chartInfo.data) {
          self.chartName = chartInfo.data.chart_name;
          self.modelName = chartInfo.data.metric_model_name;
          let record = [];
          let payload = {};
          payload["preview_data_sets"] = chartInfo.data.data_sets;
          payload["metric_id"] = self.metricId;
          this.apiService.post("/metrics/data", payload).subscribe((response) => {
            if (response.data.length !== 0) {
              let allDataSet = response.data;
              let index = 0;
              for (let oneDataSet of allDataSet) {
                for (let oneData of oneDataSet) {
                  if (!self.headers) {
                    self.headers = oneData;
                    this.data["headers"].push("input_date_time");
                    Object.keys(self.headers).forEach((key) => {
                      if (key !== "input_date_time") {
                        this.data["headers"].push(key);
                      }
                    });
                  }
                  let rowInTable = [];
                  rowInTable.push(oneData["input_date_time"]);
                  Object.keys(self.headers).forEach((key) => {
                    if (key !== "input_date_time") {
                      let value = oneData[key];
                      rowInTable.push(value);
                    }
                  });
                  self.data["rows"][index++] = rowInTable;
                }
              }

              self.data["totalLength"] = self.data["rows"].length;
              self.showingTable = true;
            }
          });

        }

      });
    }
  }
}
