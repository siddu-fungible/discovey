import { Injectable } from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";

@Injectable({
  providedIn: 'root'
})
export class PerformanceService {

  constructor(private apiService: ApiService) { }

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
        result["passedLsfJobId"] =  data.passed_lsf_job_id;
      }
      if (data.passed_git_commit && data.passed_git_commit !== "") {
        result["passedGitCommit"] = data.passed_git_commit;
      }
      return of(result);
    }));
  }

}
