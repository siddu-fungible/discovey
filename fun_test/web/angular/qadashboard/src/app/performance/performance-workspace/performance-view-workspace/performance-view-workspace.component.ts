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
  workspaceName: string = null;
  email: string = null;
  workspace: any = null;
  workspaceReport: any = null;
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
  selectMode: any = SelectMode;
  allMetricIds: number[] = [];
  interestedMetrics: any[] = [];
  SUBJECT_BASE_STRING: string = "Performance status report - ";
  TIMEZONE: string = "America/Los_Angeles";
  flattenedInterestedMetrics: any = [];

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
            return this.performanceService.getWorkspaces(this.email, this.workspaceName);
          }),
          switchMap(response => {
            this.workspace = response;
            return this.performanceService.interestedMetrics(this.workspace.id);
          }),
          switchMap(response => {
            this.workspace.interested_metrics = response;
            this.workspace.interested_metrics.forEach(metric => {
                this.flattenInterestedMetrics(metric);
            });
            return of(true);
          }),
          switchMap(response => {
            return this.performanceService.metricCharts(null, this.workspace.id);
          }),).subscribe(response => {
          console.log("fetched workspace from URL");
          this.setMetricIds(response);
        }, error => {
          this.loggerService.error("Unable to initialize workspace");
        });
      } else {
        this.loggerService.error("No workspace name and email id")
      }
    });
  }

  flattenInterestedMetrics(metric): void {
    if (metric["children"].length > 0) {
      this.flattenedInterestedMetrics.push(metric);
      for (let child of metric["children"]) {
        this.flattenInterestedMetrics(child);
      }
    } else {
      this.flattenedInterestedMetrics.push(metric);
    }
  }

  viewDag(): void {
    this.showDag = !this.showDag;
    this.reportGenerated = false;
    this.showGrids = false;
  }

  backToWorkspaces(): void {
    this.router.navigateByUrl(this.workspaceURL + "/" + this.email);
  }

  setMetricIds(charts): void {
    this.allMetricIds = [];
    this.workspaceMetrics = [];
    for (let chart of charts) {
      this.workspaceMetrics.push(Number(chart.metric_id));
    }
    this.interestedMetrics = [];
    for (let metric of this.workspace.interested_metrics) {
      let perfMetrics = {};
      perfMetrics["metric_id"] = metric["metric_id"];
      perfMetrics["lineage"] = metric["lineage"];
      this.interestedMetrics.push(perfMetrics);
    }
    this.allMetricIds = this.interestedMetrics.concat(this.workspaceMetrics);
    this.showWorkspace = true;
  }

  generateReport(): void {
    this.setSubject();
    this.showReport();
  }

  setSubject(): void {
    let t = this.commonService.convertToTimezone(new Date(), this.TIMEZONE);
    let dateString = this.commonService.getShortDate(t);
    this.subject = this.SUBJECT_BASE_STRING + dateString;
  }

  showReport(): void {
    this.reportGenerated = !this.reportGenerated;
    this.showGrids = false;
    this.showDag = false;
  }

  showCharts(): void {
    this.showGrids = !this.showGrids;
    this.reportGenerated = false;
    this.showDag = false;
  }

}
