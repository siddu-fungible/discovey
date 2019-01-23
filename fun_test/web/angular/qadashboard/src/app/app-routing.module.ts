import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardComponent }   from './dashboard/dashboard.component';
import { PerformanceComponent } from "./performance/performance.component";
import {TestComponent} from "./test/test.component";
import {FunMetricChartComponent} from "./fun-metric-chart/fun-metric-chart.component";
import {Demo1Component} from "./demo1/demo1.component";
import {RegressionComponent} from "./regression/regression.component";
import {SubmitJobComponent} from "./regression/submit-job/submit-job.component";
import {SuiteDetailComponent} from "./regression/suite-detail/suite-detail.component";
import {RegressionAdminComponent} from "./regression/regression-admin/regression-admin.component";
import {RegressionSummaryComponent} from "./regression/regression-summary/regression-summary.component";
import {ScriptHistoryComponent} from "./regression/script-history/script-history.component";

const routes: Routes = [
  { path: '', component: RegressionSummaryComponent},
  { path: 'upgrade', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'performance', component: PerformanceComponent },
  { path: 'performance/atomic/:id', component: FunMetricChartComponent},
  { path: 'regression/summary', component: RegressionSummaryComponent},
  { path: 'regression/admin', component: RegressionAdminComponent },
  { path: 'regression', component: RegressionComponent },
  { path: 'regression/jenkins_jobs', component: RegressionComponent, data: {tags: '["jenkins-hourly", "jenkins-nightly"]'}},
  { path: 'regression/jobs_by_tag/:tags', component: RegressionComponent},
  { path: 'regression/submit_job_page', component: SubmitJobComponent },
  { path: 'regression/suite_detail/:suiteId', component: SuiteDetailComponent },
  { path: 'regression/script_history_page/:scriptId', component: ScriptHistoryComponent },
  { path: 'regression/:filterString', component: RegressionComponent },
  { path: 'upgrade/test', component: TestComponent },
  { path: 'upgrade/demo1', component: Demo1Component }
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ]
})
export class AppRoutingModule {}

