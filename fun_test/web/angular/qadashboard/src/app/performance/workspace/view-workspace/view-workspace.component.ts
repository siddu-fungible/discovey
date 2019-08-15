import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../../../services/api/api.service";
import {CommonService} from "../../../services/common/common.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
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
  outputNames: any = [];
  currentChart: any = null;
  data: any = [];

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
    this.currentChart.selected = false;
  }

  openChartTable(metric): void {
    if (this.currentChart) {
      this.currentChart.selected = false;
    }
    this.data = [];
    this.status = "Fetching data";
    this.currentChart = metric;
    this.currentChart.selected = true;
    let dataSets = metric["data_sets"];
    this.outputNames = {};
    for (let dataSet of dataSets) {
      this.outputNames[dataSet["name"]] = dataSet["output"]["name"];
      let temp = {};
      temp["name"] = dataSet["name"];
      temp["today"] = null;
      temp["yesterday"] = null;
      temp["unit"] = null;
      this.data.push(temp);
    }
    let dateTime = new Date();
    this.fetchData(metric, dateTime, "today");
    dateTime.setDate(dateTime.getDate() - 1);
    this.fetchData(metric, dateTime, "yesterday");

    // new Observable(observer => {
    //   observer.next(true);
    //   observer.complete();
    //   return () => {
    //   }
    // }).pipe(
    //   switchMap(response => {
    //     return this.fetchData(metric, dateTime, "today");
    //   }),
    //   switchMap(response => {
    //     dateTime.setDate(dateTime.getDate() - 1);
    //     return this.fetchData(metric, dateTime, "yesterday");
    //   }),
    //   switchMap(response => {
    //     metric["report"] = this.data;
    //     return of(true);
    //   })).subscribe(response => {
    //   console.log("fetched today and yesterday data");
    // }, error => {
    //   this.loggerService.error("Unable to fetch today and yesterday data");
    // });

  }

  fetchData(metric, dateTime, key): any {
    let times = this.commonService.getEpochBounds(dateTime);
    let from_epoch = times[0];
    let to_epoch = times[1];
    console.log(times);
    this.apiService.get("/metrics/recent_data?metric_id=" + metric["metric_id"] + "&from_epoch=" + from_epoch + "&to_epoch=" + to_epoch).subscribe(response => {
      let data = response.data;
      for (let oneData of data) {
        for (let dataSet of this.data) {
          if (dataSet["name"] == oneData["name"]) {
            dataSet[key] = oneData["value"];
            dataSet["unit"] = oneData["unit"];
          }
        }
      }
      this.showChartTable = true;
      this.status = null;
      // return of(true);
    }, error => {
      this.loggerService.error("fetching recent data failed");
    })
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

}
