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
    this.data["totalLenght"] = this.data["rows"].length;
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
                    Object.keys(self.headers).forEach((key) => {
                      this.data["headers"].push(key);
                    });
                  }
                  let rowInTable = [];
                  Object.keys(self.headers).forEach((key) => {
                    let value = oneData[key];
                    rowInTable.push(value);
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

  describeTable(): void {
    this.inputs = [];
    this.outputList = [];
    let self = this;
    this.apiService.get("/metrics/describe_table/" + this.modelName).subscribe(function (tableInfo) {
      self.tableInfo = tableInfo.data;
      self.tableInfo.forEach((fieldInfo, field) => {
        let oneField = {};
        oneField["name"] = field;
        if ('choices' in fieldInfo && oneField["name"].startsWith("input")) {
          oneField["choices"] = fieldInfo.choices.map((choice) => {
            return choice[1]
          });
          self.inputs.push(oneField);
        }
        if (oneField["name"].startsWith("output")) {
          self.outputList.push(oneField["name"]);
        }
      });
    });
  }

  filterHeaders(headers, input): any {
    if (!headers) {
      return;
    } else {
      return headers.filter((header) => {
        if (input === "input") {
          return header.startsWith("input");
        } else {
          return header.startsWith("output");
        }
      });
    }

  }

  getVerboseName(name): string {
    return this.tableInfo[name].verbose_name;
  }


  prepareKey(valueList): string {
    let s = "";
    valueList.forEach((value) => {
      s += value;
    });
    return s;
  }

  //
  // getOutputHeaders(): any[] {
  //   let result = [];
  //   if (this.headers) {
  //     let outputHeaders = this.filterHeaders(this.headers, "output");
  //     if (outputHeaders.length > 0) {
  //       outputHeaders.forEach((outputHeader) => {
  //         this.uniqueKeys.forEach((uniqueKey) => {
  //           result.push(uniqueKey);
  //         })
  //       });
  //     }
  //
  //   }
  //   return result;
  // }
}
