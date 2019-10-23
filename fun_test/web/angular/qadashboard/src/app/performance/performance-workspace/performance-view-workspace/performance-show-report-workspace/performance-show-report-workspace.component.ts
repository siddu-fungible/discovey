import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {catchError, switchMap} from "rxjs/operators";
import {forkJoin, Observable, of} from "rxjs";
import {ApiService} from "../../../../services/api/api.service";
import {LoggerService} from "../../../../services/logger/logger.service";
import {PerformanceService} from "../../../performance.service";
import {PagerService} from "../../../../services/pager/pager.service";
import {CommonService} from "../../../../services/common/common.service";

@Component({
  selector: 'performance-show-report',
  templateUrl: './performance-show-report-workspace.component.html',
  styleUrls: ['./performance-show-report-workspace.component.css']
})
export class PerformanceShowReportWorkspaceComponent implements OnInit {
  @Input() workspace: any = null;
  @Input() flattenedInterestedMetrics: any = null;
  @Input() email: string = null;
  @Input() subject: string = null;
  @Output() reportGenerated: EventEmitter<boolean> = new EventEmitter();
  jiraUrl: string = "http://jira/browse";
  pager: any = {};
  pagedItems: any[] = [];
  showPagedItems: boolean = false;
  status: string = null;
  atomicUrl: string = "http://integration.fungible.local/performance/atomic";
  TIMEZONE: string = "America/Los_Angeles";
  historicalDataLength: number = 4;
  HISTORY: number = 10;

  constructor(private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService,
              private performanceService: PerformanceService) {
  }

  ngOnInit() {
    console.log("showing reports");
    this.status = "Loading reports info";
    new Observable(observer => {
      observer.next(true);
      //observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchScores();
      }),
      switchMap(response => {
        return this.fetchReports();
      }),
      switchMap(response => {
        return this.fetchHistory();
      })).subscribe(response => {
      this.status = null;
    }, error => {
      this.loggerService.error("Unable to initialize report component");
    });

  }

  fetchScores(): any {
    const resultObservables = [];
    this.flattenedInterestedMetrics.forEach(metric => {
      resultObservables.push(this.fetchChartInfo(metric));
    });
    if (resultObservables.length > 0) {
      return forkJoin(resultObservables);
    } else {
      return of(true);
    }
  }

  fetchChartInfo(metric): any {
    return this.performanceService.fetchChartInfo(metric.metric_id).pipe(switchMap(response => {
      let lastGoodScore = Number(response["last_good_score"]);
      let penultimateGoodScore = Number(response["penultimate_good_score"]);
      metric["last_good_score"] = lastGoodScore;
      metric["penultimate_good_score"] = penultimateGoodScore;
      metric["model_name"] = response["metric_model_name"];
      metric["data_sets"] = response["data_sets"];
      metric["jira_ids"] = response["jira_ids"];
      metric["leaf"] = response["leaf"];
      let jiraList = {};
      for (let jiraId of metric["jira_ids"]) {
        jiraList[jiraId] = {};
      }
      metric["jira_list"] = jiraList;
      metric["selected"] = false;
      metric["report"] = null;
      metric["positive"] = response["positive"];
      metric["data"] = [];
      metric["url"] = this.atomicUrl + "/" + metric["metric_id"];
      return of(true);
    }));
  }

  fetchReports(): any {
    const resultObservables = [];
    this.flattenedInterestedMetrics.forEach(metric => {
      if (!metric["report"] && metric["leaf"]) {
        resultObservables.push(this.fetchTodayAndYesterdayData(metric));
      }
    });
    if (resultObservables.length > 0) {
      return forkJoin(resultObservables);
    } else {
      return of(true);
    }
  }

  setData(metric): void {
    metric["data"] = [];
    let dataSets = metric["data_sets"];
    for (let dataSet of dataSets) {
      let temp = {};
      temp["name"] = dataSet["name"];
      temp["best"] = dataSet["best"];
      temp["today"] = null;
      temp["yesterday"] = null;
      temp["unit"] = null;
      temp["percentage"] = null;
      temp["percentage_history"] = null;
      temp["best_percentage"] = null;
      temp["history"] = [];
      temp["show_history"] = false;
      metric["data"].push(temp);
    }
  }

  fetchTodayAndYesterdayData(metric): any {
    this.setData(metric);
    let self = this;
    let dateTime = this.commonService.convertToTimezone(new Date(), this.TIMEZONE);
    return of(true).pipe(
      switchMap(response => {
        return this.fetchData(metric, dateTime, 1);
      }), catchError(error => {
        this.loggerService.error("fetching todays data failed " + error);
        throw error;
      }),
      switchMap(response => {
        dateTime.setDate(dateTime.getDate() - 1);
        return this.fetchData(metric, dateTime, 0);
      }), catchError(error => {
        this.loggerService.error("fetching yesterdays data failed " + error);
        throw error;
      }),
      switchMap(response => {
        this.calculatePercentage(metric["data"]);
        metric["report"] = metric["data"];
        return of(true);
      }), catchError(error => {
        this.loggerService.error("calculating percentage failed " + error);
        throw error;
      }));
  }

  calculatePercentage(dataSets): void {
    for (let dataSet of dataSets) {
      let percentage = "NA";
      let bestPercentage = "NA";
      if (dataSet["today"] && dataSet["yesterday"]) {
        let today = Number(dataSet["today"]);
        let yesterday = Number(dataSet["yesterday"]);
        let percentNum = (((today - yesterday) / yesterday) * 100);
        percentage = percentNum.toFixed(2) + "%";
        if (percentNum >= 0) {
          percentage = "+" + percentage;
        }
      }
      if (dataSet["today"] && dataSet["best"] && dataSet["best"] != -1) {
        let today = Number(dataSet["today"]);
        let best = Number(dataSet["best"]);
        let percentNum = (((today - best) / best) * 100);
        bestPercentage = percentNum.toFixed(2) + "%";
        if (percentNum >= 0) {
          bestPercentage = "+" + bestPercentage;
        }
      }
      dataSet["percentage"] = percentage;
      dataSet["best_percentage"] = bestPercentage;
    }
  }

  fetchData(metric, dateTime, today): any {
    let times = this.commonService.getEpochBounds(dateTime);
    let fromEpoch = times[0];
    let toEpoch = times[1];
    let self = this;
    let key = "";
    if (today) {
      key = "today";
    } else {
      key = "yesterday";
    }
    return this.apiService.get("/api/v1/performance/metrics_data?metric_id=" + metric["metric_id"] + "&from_epoch_ms=" + fromEpoch + "&to_epoch_ms=" + toEpoch).pipe(switchMap(response => {
      let data = response.data;
      for (let oneData of data) {
        for (let dataSet of metric["data"]) {
          if (dataSet["name"] == oneData["name"]) {
            dataSet[key] = oneData["value"];
            dataSet[key + "Date"] = this.commonService.getPrettyPstTime(oneData["date_time"]);
            dataSet["unit"] = oneData["unit"];
          }
        }
      }
      return of(true);
    }));
  }

  fetchHistory(): any {
    const resultObservables = [];
    this.flattenedInterestedMetrics.forEach(metric => {
      if (metric["leaf"]) {
        resultObservables.push(this.fetchHistoricalData(metric));
      }
    });
    if (resultObservables.length > 0) {
      return forkJoin(resultObservables);
    } else {
      return of(true);
    }
  }

  fetchHistoricalData(metric): any {
    return this.apiService.get("/api/v1/performance/metrics_data?metric_id=" + metric["metric_id"] + "&order_by=-input_date_time&count=" + this.HISTORY).pipe(switchMap(response => {
      let data = response.data;
      for (let dataSet of metric["data"]) {
        dataSet["history"] = [];
        let dateTimeSet = new Set();
        for (let oneData of data) {
          if (dataSet["name"] == oneData["name"]) {
            let present = this.addToSet(oneData["date_time"], dateTimeSet);
            if (!present) {
              let hData = {};
              hData["date"] = this.commonService.getPrettyPstTime(oneData["date_time"]);
              hData["value"] = oneData["value"];
              dataSet["history"].push(hData);
            }
            if (dataSet["history"].length > this.historicalDataLength) {
              break;
            }
          }
        }
        let maximum = 0;
        let hData = {};
        dataSet["best_value"] = {};
        for (let oneHistoricalData of data) {
          if (dataSet["name"] == oneHistoricalData["name"]) {
            if (oneHistoricalData["value"] > maximum) {
              hData["date"] = this.commonService.getPrettyPstTime(oneHistoricalData["date_time"]);
              hData["value"] = oneHistoricalData["value"];
            }
          }
        }
        dataSet["best_value"] = hData;
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

  addToSet(dateTime, dateTimeSet): boolean {
    let dateTimeObj = this.commonService.convertToTimezone(dateTime, this.TIMEZONE);
    let dateTimeStr = String(dateTimeObj.getMonth() + 1) + "/" + String(dateTimeObj.getDate()) + "/" + String(dateTimeObj.getFullYear());
    let present = false;
    if (dateTimeSet.has(dateTimeStr)) {
      present = true;
    } else {
      dateTimeSet.add(dateTimeStr)
    }
    return present
  }

  refreshPage(): void {
    this.pagedItems = this.flattenedInterestedMetrics.slice(this.pager.startIndex, this.pager.endIndex + 1);
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
    this.flattenedInterestedMetrics.forEach(metric => {
      if (metric["report"] && metric["leaf"]) {
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
