import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {switchMap} from "rxjs/operators";
import {Observable, of} from "rxjs";
import {ApiService} from "../../../../services/api/api.service";
import {LoggerService} from "../../../../services/logger/logger.service";
import {PerformanceService} from "../../../performance.service";
import {PagerService} from "../../../../services/pager/pager.service";

@Component({
  selector: 'performance-show-report',
  templateUrl: './performance-show-report-workspace.component.html',
  styleUrls: ['./performance-show-report-workspace.component.css']
})
export class PerformanceShowReportWorkspaceComponent implements OnInit {
  @Input() workspace: any = null;
  @Input() email: string = null;
  @Input() subject: string = null;
  @Output() reportGenerated: EventEmitter<boolean> = new EventEmitter();
  jiraUrl: string = "http://jira/browse";
  pager: any = {};
  currentPage: number = 1;
  RECORDS_PER_PAGE: number = 5;
  pagedItems: any[] = [];

  constructor(private apiService: ApiService, private loggerService: LoggerService, private performanceService: PerformanceService, private pagerService: PagerService) {
  }

  ngOnInit() {
    this.refreshPage();
  }

  refreshPage(): void {
    this.pager = this.pagerService.getPager(this.workspace.interested_metrics.length, this.currentPage, this.RECORDS_PER_PAGE);
    this.pagedItems = this.workspace.interested_metrics.slice(this.pager.startIndex, this.pager.endIndex + 1);
  }

  setPage(pageNumber): void {
    this.currentPage = pageNumber;
    this.refreshPage()
  }

  saveComments(): any {
    let payload = {};
    payload["email"] = this.email;
    payload["workspace_id"] = this.workspace.id;
    payload["interested_metrics"] = this.workspace.interested_metrics;
    return this.performanceService.saveInterestedMetrics(this.workspace.id, payload)
  }

  sendReports(): void {
    new Observable(observer => {
      observer.next(true);
      //observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.saveComments();
      }),
      switchMap(response => {
        return this.sendEmail();
      })).subscribe(response => {
      if (response["status"]) {
        this.loggerService.success("sent report email successfully to " + this.email);
      } else {
        this.loggerService.error("sending email failed");
      }

    }, error => {
      this.loggerService.error("sending email failed");
    });
  }

  sendEmail(): any {
    let payload = {};
    let reports = [];
    this.workspace.interested_metrics.forEach(metric => {
      let report = {};
      report["chart_name"] = metric["chart_name"];
      report["lineage"] = metric["lineage"];
      report["url"] = metric["url"];
      report["comments"] = metric["comments"];
      report["jira_ids"] = metric["jira_ids"];
      report["report"] = metric["report"];
      report["positive"] = metric["positive"];
      reports.push(report);
    });
    payload["reports"] = reports;
    payload["email"] = this.email;
    payload["subject"] = this.subject;
    return this.performanceService.sendEmail(payload);
  }

}
