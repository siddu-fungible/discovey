import {NgModule} from '@angular/core';
import {RouterModule, Routes, UrlSegment} from '@angular/router';

import {DashboardComponent} from './dashboard/dashboard.component';
import {PerformanceComponent} from "./performance/performance.component";
import {TestComponent} from "./test/test.component";
import {FunMetricChartComponent} from "./fun-metric-chart/fun-metric-chart.component";
import {RegressionComponent} from "./regression/regression.component";
import {SubmitJobComponent} from "./regression/submit-job/submit-job.component";
import {SuiteDetailComponent} from "./regression/suite-detail/suite-detail.component";
import {RegressionAdminComponent} from "./regression/regression-admin/regression-admin.component";
import {RegressionSummaryComponent} from "./regression/regression-summary/regression-summary.component";
import {TriageComponent} from "./triage/triage.component";
import {ScriptHistoryComponent} from "./regression/script-history/script-history.component";
import {NotFoundComponent} from "./not-found/not-found.component";
import {AlertsComponent} from "./alerts/alerts.component";
import {SchedulerAdminComponent} from "./scheduler-admin/scheduler-admin.component";
import {LogViewerComponent} from "./log-viewer/log-viewer.component";
import {UserComponent} from "./user/user.component";
import {TestBedComponent} from "./regression/test-bed/test-bed.component";
import {JirasComponent} from "./regression/jiras/jiras.component";
import {JobSpecComponent} from "./regression/job-spec/job-spec.component";
import {Triage2Component} from "./regression/triage2/triage2.component";
import {JenkinsFormComponent} from "./jenkins-form/jenkins-form.component";
import {TriageDetailComponent} from "./regression/triage2/triage-detail/triage-detail.component";
import {AdminComponent} from "./performance/admin/admin.component";
import {CreateChartComponent} from "./performance/create-chart/create-chart.component";
import {ScoresTableComponent} from "./performance/scores-table/scores-table.component";
import {PerformanceTableComponent} from "./performance/performance-table/performance-table.component";
import {PerformanceWorkspaceComponent} from './performance/performance-workspace/performance-workspace.component';
import {PerformanceViewWorkspaceComponent} from "./performance/performance-workspace/performance-view-workspace/performance-view-workspace.component";
import {SuiteEditorComponent} from "./regression/suite-editor/suite-editor.component";
import {SuitesViewComponent} from "./regression/suite-editor/suites-view/suites-view.component";
import {ScriptDetailComponent} from "./regression/script-detail/script-detail.component";
import {ReleaseCatalogEditorComponent} from "./regression/release-catalog-editor/release-catalog-editor.component";
import {ReleasesComponent} from "./regression/releases/releases.component";
import {ReleaseCatalogsComponent} from "./regression/release-catalogs/release-catalogs.component";
import {DaemonsComponent} from "./daemons/daemons.component";
import {BrokerTestComponent} from "./mq-broker/broker-test/broker-test.component";
import {ReleaseDetailComponent} from "./regression/release-detail/release-detail.component";
import {LoginComponent} from "./login/login.component";
import {LastGoodBuildComponent} from "./regression/last-good-build/last-good-build.component";

export function regressionHome(url: UrlSegment[]) {
  return url[0].path.endsWith("regression");
}


const routes: Routes = [
  {path: '', component: DashboardComponent},
  {path: 'upgrade', component: DashboardComponent},
  {path: 'users', component: UserComponent},
  {path: 'dashboard', component: DashboardComponent},
  {path: 'performance', component: PerformanceComponent},
  {path: 'performance/workspace', component: PerformanceWorkspaceComponent},
  {path: 'performance/workspace/:emailId', component: PerformanceWorkspaceComponent},
  {path: 'performance/workspace/:emailId/:name', component: PerformanceViewWorkspaceComponent},
  {path: 'performance/atomic/:id', component: FunMetricChartComponent},
  {path: 'regression/summary', component: RegressionSummaryComponent},
  {path: 'regression/admin', component: RegressionAdminComponent},
  {path: 'regression/all_jiras_component', component: JirasComponent},
  {path: 'regression', component: RegressionComponent},
  {path: 'regression/jobs_by_tag/:tags', component: RegressionComponent},
  {path: 'regression/submit_job_page', component: SubmitJobComponent},
  {path: 'regression/test_bed', component: TestBedComponent},
  {path: 'regression/suite_detail/:suiteExecutionId', component: SuiteDetailComponent},
  {path: 'regression/script_detail/:scriptId/:logPrefix/:suiteExecutionId', component: ScriptDetailComponent},
  {path: 'regression/script_history_page/:scriptId', component: ScriptHistoryComponent},
  {path: 'regression/job_spec_detail/:id', component: JobSpecComponent},
  {path: 'regression/suite_editor/:id', component: SuiteEditorComponent},
  {path: 'regression/suite_editor', component: SuiteEditorComponent},
  {path: 'regression/suites_view', component: SuitesViewComponent},
  {path: 'regression', component: RegressionComponent},
  {path: 'regression/scheduler/admin', component: SchedulerAdminComponent},
  {path: 'common/alerts', component: AlertsComponent},
  {path: 'common/logs', component: LogViewerComponent},
  {path: 'upgrade/test', component: TestComponent},
  {path: '*', component: NotFoundComponent},
  { path: 'performance/atomic/:id/triage', component: TriageComponent},
  { path: 'regression/triaging/:id', component: TriageDetailComponent},
  { path: 'regression/triaging', component: Triage2Component},
  { path: 'regression/release_catalog_editor', component: ReleaseCatalogEditorComponent},
  { path: 'regression/releases', component: ReleasesComponent},
  { path: 'regression/release_catalogs', component: ReleaseCatalogsComponent},
  { path: 'regression/release_detail/:executionId', component: ReleaseDetailComponent},
  { path: 'regression/last_good_build', component: LastGoodBuildComponent},
  { path: 'performance/admin/scores/:metricId', component: ScoresTableComponent},
  { path: 'performance/admin/data/:metricId', component: PerformanceTableComponent},
  { path: 'performance/admin/:mode/:modelName/:metricId', component: CreateChartComponent},
  { path: 'performance/admin/:mode/:modelName', component: CreateChartComponent},
  { path: 'performance/admin', component: AdminComponent},
  { path: 'performance/score_table/:metricId', component: ScoresTableComponent},
  {path: 'daemons', component: DaemonsComponent},
  {path: 'mq_broker/broker-test', component: BrokerTestComponent},
  {path: 'login', component: LoginComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}

