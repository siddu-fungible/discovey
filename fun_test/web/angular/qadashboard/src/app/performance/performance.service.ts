import {Injectable} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {CommonService} from "../services/common/common.service";

export enum SelectMode {
  None = 0,
  ShowMainSite = 1,
  ShowEditWorkspace = 2,
  ShowViewWorkspace = 3,
  ShowAttachDag = 4
}

interface  JobRunTimeProperties {
  date_time: any;
  run_time: any;
}

export class JobRunTime implements JobRunTimeProperties {
  date_time: any;
  run_time: any;

  constructor(obj?: any) {
    Object.assign(this, obj);
  }
}

@Injectable({
  providedIn: 'root'
})

export class PerformanceService {
  buildInfo: any = null;
  TIMEZONE: string = "America/Los_Angeles";

  constructor(private apiService: ApiService, private commonService: CommonService) {
  }

  chartInfo(metricId) {
    let payload = {"metric_id": metricId};
    return this.apiService.post('/metrics/chart_info', payload).pipe(switchMap((response) => {
      let data = response.data;
      let result = {};
      if (data.last_suite_execution_id && data.last_suite_execution_id !== -1) {
        result["lastSuiteExecutionId"] = data.last_suite_execution_id;
      }
      if (data.last_jenkins_job_id && data.last_jenkins_job_id !== -1) {
        result["lastJenkinsJobId"] = data.last_jenkins_job_id;
      }
      if (data.last_lsf_job_id && data.last_lsf_job_id !== -1) {
        result["lastLsfJobId"] = data.last_lsf_job_id;
      }
      if (data.last_git_commit && data.last_git_commit !== "") {
        result["currentGitCommit"] = data.last_git_commit;
      }
      return of(result);
    }));
  }

  pastStatus(metricId) {
    let payload = {"metric_id": metricId};

    return this.apiService.post('/metrics/past_status', payload).pipe(switchMap((response) => {
      let data = response.data;
      let result = {};

      if (data.failed_date_time) {
        result["failedDateTime"] = data.failed_date_time;
      }
      if (data.failed_suite_execution_id && data.failed_suite_execution_id !== -1) {
        result["failedSuiteExecutionId"] = data.failed_suite_execution_id;
      }
      if (data.failed_jenkins_job_id && data.failed_jenkins_job_id !== -1) {
        result["failedJenkinsJobId"] = data.failed_jenkins_job_id;
      }
      if (data.failed_lsf_job_id && data.failed_lsf_job_id !== -1) {
        result["failedLsfJobId"] = data.failed_lsf_job_id;
      }
      if (data.failed_git_commit && data.failed_git_commit !== "") {
        result["failedGitCommit"] = data.failed_git_commit;
      }
      if (data.passed_date_time) {
        result["passedDateTime"] = data.passed_date_time;
      }
      if (data.passed_suite_execution_id && data.passed_suite_execution_id !== -1) {
        result["passedSuiteExecutionId"] = data.passed_suite_execution_id;
      }
      if (data.passed_jenkins_job_id && data.passed_jenkins_job_id !== -1) {
        result["passedJenkinsJobId"] = data.passed_jenkins_job_id;
      }
      if (data.passed_lsf_job_id && data.passed_lsf_job_id !== -1) {
        result["passedLsfJobId"] = data.passed_lsf_job_id;
      }
      if (data.passed_git_commit && data.passed_git_commit !== "") {
        result["passedGitCommit"] = data.passed_git_commit;
      }
      return of(result);
    }));
  }

  //populates buildInfo
  fetchBuildInfo(): any {
    return this.apiService.get('/regression/build_to_date_map').pipe(switchMap(response => {
      if (this.buildInfo) {
        return of(this.buildInfo)
      } else {
        this.buildInfo = response.data;
        return of(this.buildInfo);
      }
    }));
  }

  saveInterestedMetrics(workspaceId, payload): any {
    return this.apiService.post("/api/v1/performance/workspaces/" + workspaceId + "/interested_metrics", payload).pipe(switchMap(response => {
      return of(true);
    }));
  }

  sendEmail(payload): any {
    return this.apiService.post('/api/v1/performance/reports', payload).pipe(switchMap(response => {
      return of(response.data);
    }));
  }

  metricCharts(metricId, workspaceId): any {
    return this.apiService.get("/api/v1/performance/metric_charts" + "?workspace_id=" + workspaceId).pipe(switchMap(response => {
      return of(response.data);
    }));
  }

  metricsData(metricId, fromEpoch, toEpoch): any {
    return this.apiService.get("/api/v1/performance/metrics_data?metric_id=" + metricId + "&from_epoch_ms=" + fromEpoch + "&to_epoch_ms=" + toEpoch).pipe(switchMap(response => {
      return of(response.data);
    }));
  }

  interestedMetrics(workspaceId): any {
    return this.apiService.get("/api/v1/performance/workspaces/" + workspaceId + "/interested_metrics").pipe(switchMap(response => {
      return of(response.data);
    }));
  }

  getWorkspaces(email, workspaceName): any {
    return this.apiService.get("/api/v1/performance/workspaces?email=" + email + "&workspace_name=" + workspaceName).pipe(switchMap(response => {
      return of(response.data[0]);
    }));
  }

  fetchChartInfo(metricId): any {
    let payload = {};
    payload["metric_id"] = metricId;
    return this.apiService.post("/metrics/chart_info", payload).pipe(switchMap(response => {
      return of(response.data);
    }));
  }

  fetchRunTimeProperties(id): any {
    let payload = {};
    payload["id"] = id;
    return this.apiService.post("/metrics/run_time", payload).pipe(switchMap(response => {
      return of(new JobRunTime(response.data));
    }));
  }

}
