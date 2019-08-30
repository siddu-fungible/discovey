import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../../../services/api/api.service";
import {CommonService} from "../../../services/common/common.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {forkJoin, from, Observable, of} from "rxjs";
import {concatMap, mergeMap, switchMap} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";
import {Location} from '@angular/common';
import {Title} from "@angular/platform-browser";
import {PerformanceService} from "../../performance.service";
import {SelectMode} from "../../performance.service";

@Component({
  selector: 'view-workspace',
  templateUrl: './performance-view-workspace.component.html',
  styleUrls: ['./performance-view-workspace.component.css']
})
export class PerformanceViewWorkspaceComponent implements OnInit {
  buildInfo: any = null;
  workspaceName: string = null;
  email: string = null;
  workspace: any = null;
  showWorkspace: boolean = false;
  showGrids: boolean = false;
  showChartTable: boolean = false;
  status: string = null;
  currentChart: any = null;
  data: any = [];
  atomicUrl: string = "http://integration.fungible.local/performance/atomic";
  jiraUrl: string = "http://jira/browse";
  workspaceURL: string = "/performance/workspace";
  reportGenerated: boolean = false;
  subject: string = null;
  workspaceMetrics: number[] = [];
  showDag: boolean = false;
  selectMode: any = SelectMode.showAttachDag;
  allMetricIds: number[] = [];
  interestedMetrics: number[] = [];

  constructor(private apiService: ApiService, private commonService: CommonService, private loggerService: LoggerService,
              private route: ActivatedRoute, private router: Router, private location: Location, private title: Title, private performanceService: PerformanceService) {
  }

  ngOnInit() {
    this.title.setTitle("Workspace");
    this.route.params.subscribe(params => {
      if (params['emailId'] && params['name']) {
        this.email = params["emailId"];
        this.workspaceName = params["name"];
        new Observable(observer => {
          observer.next(true);
          observer.complete();
          return () => {
          }
        }).pipe(
          switchMap(response => {
            return this.fetchWorkspaces();
          }),
          switchMap(response => {
            return this.fetchInterestedMetrics(this.workspace.id);
          }),
          switchMap(response => {
            return this.fetchScores();
          }),
          switchMap(response => {
            return this.performanceService.fetchBuildInfo();
          }),
          switchMap(response => {
            return this.fetchMetricIdsByWorkspace(this.workspace.id);
          }),).subscribe(response => {
          this.buildInfo = response;
          console.log("fetched workspace and buildInfo from URL");
          this.showWorkspace = true;
        }, error => {
          this.loggerService.error("Unable to initialize workspace");
        });
      } else {
        this.loggerService.error("No workspace name and email id")
      }
    });
  }

  goBack(): void {
    this.location.back();
  }

  viewDag(): void {
    this.showDag = true;
    this.reportGenerated = false;
    this.showGrids = false;
  }

  backToWorkspaces(): void {
    this.router.navigateByUrl(this.workspaceURL + "/" + this.email);
  }

  fetchWorkspaces(): any {
    return this.apiService.get("/api/v1/performance/workspaces/" + this.email + "/" + this.workspaceName).pipe(switchMap(response => {
      this.workspace = response.data[0];
      return of(true);
    }));
  }

  fetchMetricIdsByWorkspace(workspaceId): any {
    return this.apiService.get("/api/v1/performance/workspaces/" + workspaceId + "/metric_ids").pipe(switchMap(response => {
      this.allMetricIds = [];
      this.workspaceMetrics = response.data;
      this.interestedMetrics = [];
      for (let metric of this.workspace.interested_metrics) {
        this.interestedMetrics.push(metric["metric_id"])
      }
      this.allMetricIds = this.interestedMetrics.concat(this.workspaceMetrics);
      return of(true);
    }));
  }

  // fetchWorkspaceDags(workspaceId): any {
  //   return this.apiService.get("/api/v1/performance/workspaces/" + workspaceId + "/dags").pipe(switchMap(response => {
  //     this.workspace.interested_metrics = response.data;
  //     return of(true);
  //   }));
  // }

  fetchInterestedMetrics(workspaceId): any {
    return this.apiService.get("/api/v1/performance/workspaces/" + workspaceId + "/interested_metrics").pipe(switchMap(response => {
      this.workspace.interested_metrics = response.data;
      return of(true);
    }));
  }

  closeChartTable(): void {
    this.showChartTable = false;
    if (this.currentChart) {
      this.currentChart.selected = false;
    }
  }

  openChartTable(metric): void {
    this.closeChartTable();
    this.status = "Fetching data";
    this.currentChart = metric;
    this.currentChart.selected = true;
    if (!metric["report"]) {
      let obsObj = this.fetchTodayAndYesterdayData(metric);
      obsObj.subscribe(response => {
        console.log("fetched today and yesterday data");
      }, error => {
        this.loggerService.error("Unable to fetch today and yesterday data when opened chart");
      });
    }
    this.showChartTable = true;
    this.status = null;
  }

  setData(metric): void {
    metric["data"] = [];
    let dataSets = metric["data_sets"];
    for (let dataSet of dataSets) {
      let temp = {};
      temp["name"] = dataSet["name"];
      temp["today"] = null;
      temp["yesterday"] = null;
      temp["unit"] = null;
      temp["percentage"] = null;
      temp["history"] = [];
      metric["data"].push(temp);
    }
  }

  fetchTodayAndYesterdayData(metric): any {
    this.setData(metric);
    let self = this;
    let dateTime = new Date();
    return of(true).pipe(
      switchMap(response => {
        return this.fetchData(metric, dateTime, "today");
      }),
      switchMap(response => {
        dateTime.setDate(dateTime.getDate() - 1);
        return this.fetchData(metric, dateTime, "yesterday");
      }),
      switchMap(response => {
        this.calculatePercentage(metric["data"]);
        metric["report"] = metric["data"];
        return of(true);
      }));
  }

  calculatePercentage(dataSets): void {
    for (let dataSet of dataSets) {
      let percentage = "NA";
      if (dataSet["today"] && dataSet["yesterday"]) {
        let today = Number(dataSet["today"]);
        let yesterday = Number(dataSet["yesterday"]);
        let percentNum = (((today - yesterday) / yesterday) * 100);
        percentage = percentNum.toFixed(2) + "%";
        if (percentNum >= 0) {
          percentage = "+" + percentNum.toFixed(2) + "%";
        }
      }
      dataSet["percentage"] = percentage;
    }
  }

  fetchData(metric, dateTime, key): any {
    let times = this.commonService.getEpochBounds(dateTime);
    let from_epoch = times[0];
    let to_epoch = times[1];
    let self = this;
    return this.apiService.get("/api/v1/performance/metrics_data?metric_id=" + metric["metric_id"] + "&from_epoch_ms=" + from_epoch + "&to_epoch_ms=" + to_epoch).pipe(switchMap(response => {
      let data = response.data;
      for (let oneData of data) {
        for (let dataSet of metric["data"]) {
          if (dataSet["name"] == oneData["name"]) {
            dataSet[key] = oneData["value"];
            dataSet[key + "Date"] = this.commonService.getPrettyLocalizeTime(oneData["date_time"]);
            dataSet["unit"] = oneData["unit"];
          }
        }
      }
      return of(true);
    }));
  }

  fetchScores(): any {
    for (let metric of this.workspace.interested_metrics) {
      let payload = {};
      payload["metric_id"] = metric.metric_id;
      this.apiService.post("/metrics/chart_info", payload).subscribe(response => {
        let lastGoodScore = Number(response.data["last_good_score"]);
        let penultimateGoodScore = Number(response.data["penultimate_good_score"]);
        metric["last_good_score"] = lastGoodScore;
        metric["penultimate_good_score"] = penultimateGoodScore;
        metric["model_name"] = response.data["metric_model_name"];
        metric["data_sets"] = response.data["data_sets"];
        metric["jira_ids"] = response.data["jira_ids"];
        let jiraList = {};
        for (let jiraId of metric["jira_ids"]) {
          jiraList[jiraId] = {};
        }
        metric["jira_list"] = jiraList;
        metric["selected"] = false;
        metric["report"] = null;
        metric["positive"] = response.data["positive"];
        metric["data"] = [];
        metric["url"] = this.atomicUrl + "/" + metric["metric_id"];
      }, error => {
        this.loggerService.error("failed fetching the chart info while viewing workspace");
      });
    }
    return of(true);
  }

  fetchReports(): any {
    const resultObservables = [];
    this.workspace.interested_metrics.forEach(metric => {
      if (!metric["report"]) {
        resultObservables.push(this.fetchTodayAndYesterdayData(metric));
      }
    });
    if (resultObservables.length > 0) {
      return forkJoin(resultObservables);
    } else {
      return of(true);
    }
  }

  fetchHistory(): any {
    const resultObservables = [];
    this.workspace.interested_metrics.forEach(metric => {
      resultObservables.push(this.fetchHistoricalData(metric));
    });
    if (resultObservables.length > 0) {
      return forkJoin(resultObservables);
    } else {
      return of(true);
    }
  }

  fetchHistoricalData(metric): any {
    return this.apiService.get("/api/v1/performance/metrics_data?metric_id=" + metric["metric_id"] + "&order_by=-input_date_time&count=5").pipe(switchMap(response => {
      let data = response.data;
      for (let dataSet of metric["data"]) {
        dataSet["history"] = [];
        for (let oneData of data) {
          if (dataSet["name"] == oneData["name"]) {
            let hData = {};
            hData["date"] = this.commonService.getPrettyLocalizeTime(oneData["date_time"]);
            hData["value"] = oneData["value"];
            dataSet["history"].push(hData);
          }
        }
        dataSet["rows"] = dataSet["history"].length + 1;
        let percentage = "NA";
        if (dataSet["history"].length >= 2) {
          let lastValue = Number(dataSet["history"][0].value);
          let penultimateValue = Number(dataSet["history"][1].value);
          let percentNum = (((lastValue - penultimateValue) / penultimateValue) * 100);
          percentage = percentNum.toFixed(2) + "%";
          if (percentNum >= 0) {
            percentage = "+" + percentage;
          }
        }
        dataSet["percentage_history"] = percentage;
      }
      return of(true);
    }));
  }

  generateReport(): void {
    new Observable(observer => {
      observer.next(true);
      //observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchReports();
      }),
      switchMap(response => {
        return this.fetchHistory();
      })).subscribe(response => {
      let t = new Date();
      let dateString = this.commonService.getShortDate(t);
      this.subject = "Performance status report - " + dateString;
      this.reportGenerated = true;
      this.showGrids = false;
      this.showDag = false;
    }, error => {
      this.loggerService.error("Unable to generate report");
    });

  }

  showCharts(): void {
    this.showGrids = true;
    this.reportGenerated = false;
    this.showDag = false;
  }

}
