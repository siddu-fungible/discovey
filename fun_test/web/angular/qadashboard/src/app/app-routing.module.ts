import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardComponent }   from './dashboard/dashboard.component';
import { PerformanceComponent } from "./performance/performance.component";
import {TestComponent} from "./test/test.component";
import {FunMetricChartComponent} from "./fun-metric-chart/fun-metric-chart.component";
import {Demo1Component} from "./demo1/demo1.component";
import {RegressionComponent} from "./regression/regression.component";
import {SubmitJobComponent} from "./regression/submit-job/submit-job.component";

const routes: Routes = [
  { path: 'upgrade', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'performance', component: PerformanceComponent },
  { path: 'performance/atomic/:id', component: FunMetricChartComponent},
  { path: 'upgrade/regression', component: RegressionComponent },
  { path: 'upgrade/regression/jenkins_jobs', component: RegressionComponent, data: {tags: '["jenkins-hourly", "jenkins-nightly"]'}},
  { path: 'upgrade/regression/jobs_by_tag/:tags', component: RegressionComponent},
  { path: 'upgrade/regression/submit_job_page', component: SubmitJobComponent },
  { path: 'upgrade/regression/:filterString', component: RegressionComponent },
  { path: 'upgrade/test', component: TestComponent },
  { path: 'upgrade/demo1', component: Demo1Component }
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ]
})
export class AppRoutingModule {}

