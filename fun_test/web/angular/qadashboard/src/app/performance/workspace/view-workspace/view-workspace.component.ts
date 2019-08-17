import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../../../services/api/api.service";
import {CommonService} from "../../../services/common/common.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {forkJoin, from, Observable, of} from "rxjs";
import {concatMap, mergeMap, switchMap} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";
import {Location} from '@angular/common';
import {Title} from "@angular/platform-browser";

@Component({
  selector: 'view-workspace',
  templateUrl: './view-workspace.component.html',
  styleUrls: ['./view-workspace.component.css']
})
export class ViewWorkspaceComponent implements OnInit {
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
  atomicUrl: string = "/performance/atomic/";

  constructor(private apiService: ApiService, private commonService: CommonService, private loggerService: LoggerService,
              private route: ActivatedRoute, private router: Router, private location: Location, private title: Title) {
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
            return this.fetchInterestedMetrics(this.workspace.workspace_id);
          }),
          switchMap(response => {
            return this.fetchScores();
          }),
          switchMap(response => {
            return this.fetchBuildInfo();
          })).subscribe(response => {
          console.log("fetched workspace and buildInfo from URL");
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

  fetchWorkspaces(): any {
    return this.apiService.get("/api/v1/workspaces/" + this.email + "/" + this.workspaceName).pipe(switchMap(response => {
      this.workspace = response.data[0];
      return of(true);
    }));
  }

  fetchInterestedMetrics(workspaceId): any {
    return this.apiService.get("/api/v1/workspaces/" + workspaceId + "/interested_metrics").pipe(switchMap(response => {
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
      temp["chart_name"] = metric["chart_name"];
      temp["url"] = this.atomicUrl + metric["metric_id"];
      temp["lineage"] = metric["lineage"];
      temp["metric_id"] = metric["metric_id"];
      metric["data"].push(temp);
    }
  }

  fetchTodayAndYesterdayData(metric): any {
    this.setData(metric);
    let self = this;
    let dateTime = new Date();
    dateTime.setDate(dateTime.getDate() - 1);
    return of(true).pipe(
      switchMap(response => {
        return this.fetchData(metric, dateTime, "today");
      }),
      switchMap(response => {
        dateTime.setDate(dateTime.getDate() - 2);
        return this.fetchData(metric, dateTime, "yesterday");
      }),
      switchMap(response => {
        this.calculatePercentage(metric);
        metric["report"] = metric["data"];
        return of(true);
      }));
  }

  calculatePercentage(metric): void {
    for (let dataSet of metric["data"]) {
      let percentage = "NA";
      if (dataSet["today"] && dataSet["yesterday"]) {
        let today = Number(dataSet["today"]);
        let yesterday = Number(dataSet["yesterday"]);
        let percentNum = (((today - yesterday) / yesterday) * 100);
        if (percentNum >= 0) {
          percentage = "+" + percentNum.toFixed(2) + "%";
        } else {
          percentage = percentNum.toFixed(2) + "%";
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
    console.log(times);
    return this.apiService.get("/api/v1/performance/report_data?metric_id=" + metric["metric_id"] + "&from_epoch_ms=" + from_epoch + "&to_epoch_ms=" + to_epoch).pipe(switchMap(response => {
      let data = response.data;
      for (let oneData of data) {
        for (let dataSet of metric["data"]) {
          if (dataSet["name"] == oneData["name"]) {
            dataSet[key] = oneData["value"];
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
        metric["selected"] = false;
        metric["report"] = null;
        metric["data"] = [];
      }, error => {
        this.loggerService.error("failed fetching the chart info while viewing workspace");
      });
    }
    return of(true);
  }

  //populates buildInfo
  fetchBuildInfo(): any {
    return this.apiService.get('/regression/build_to_date_map').pipe(switchMap(response => {
      this.buildInfo = {};
      Object.keys(response.data).forEach((key) => {
        let localizedKey = this.commonService.convertToLocalTimezone(key);
        this.buildInfo[this.commonService.addLeadingZeroesToDate(localizedKey)] = response.data[key];
      });
      this.showWorkspace = true;
      return of(true);
    }));
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

  sendReports(): any {
    let payload = {};
    let reports = [];
    this.workspace.interested_metrics.forEach(metric => {
      let report = {};
      report[metric["chart_name"]] = metric["report"];
      reports.push(report);
    });
    payload["reports"] = reports;
    payload["email"] = this.email;
    let today = new Date();
    let m =  ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    payload["subject"] = "Daily TeraMark status update - " + String(today.getDate()) + " " + String(m[today.getMonth()]);
    return this.apiService.post('/api/v1/performance/report_data', payload).pipe(switchMap(response => {
      if (response.data["status"]) {
        this.loggerService.success("sent report email successfully to " + this.email);
      } else {
        this.loggerService.error("sending email fialed");
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
        return this.sendReports();
      })).subscribe(response => {
      console.log("generated report and sent to " + this.email);
    }, error => {
      this.loggerService.error("Unable to generate report");
    });

  }

}
