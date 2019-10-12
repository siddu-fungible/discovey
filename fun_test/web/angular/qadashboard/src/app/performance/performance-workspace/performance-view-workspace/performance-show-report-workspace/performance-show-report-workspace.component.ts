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
  pagedItems: any[] = [];
  showPagedItems: boolean = false;

  constructor(private apiService: ApiService, private loggerService: LoggerService, private performanceService: PerformanceService) {
  }

  ngOnInit() {
    console.log("showing reports");
  }

  refreshPage(): void {
    this.pagedItems = this.workspace.interested_metrics.slice(this.pager.startIndex, this.pager.endIndex + 1);
    this.showPagedItems = true;
  }

  setPage(pager): void {
    this.pager = pager;
    setTimeout(() => {
      this.refreshPage();
    }, 1);
  }

  saveComments(): any {
    let payload = {};
    payload["email"] = this.email;
    payload["workspace_id"] = this.workspace.id;
    payload["interested_metrics"] = this.workspace.interested_metrics;
    return of(true);
    // return this.performanceService.saveInterestedMetrics(this.workspace.id, payload)
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
      if (!metric["report"] && metric["leaf"]) {
        let report = {};
        report["chart_name"] = metric["chart_name"];
        report["lineage"] = metric["lineage"];
        report["url"] = metric["url"];
        report["comments"] = metric["comments"];
        report["jira_ids"] = metric["jira_ids"];
        report["report"] = metric["report"];
        report["positive"] = metric["positive"];
        reports.push(report);
      }
    });
    payload["reports"] = reports;
    payload["email"] = this.email;
    payload["subject"] = this.subject;
    return this.performanceService.sendEmail(payload);
  }

}
