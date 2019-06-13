import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import {MatSortModule} from '@angular/material';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';

import { AppComponent } from './app.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { AppRoutingModule }     from './app-routing.module';
import { PerformanceComponent } from './performance/performance.component';
import { HttpClientModule } from '@angular/common/http';
import { FunTableComponent } from './fun-table/fun-table.component';
import { ApiService } from "./services/api/api.service";
import { LoggerService } from "./services/logger/logger.service";
import { TestComponent } from './test/test.component';
import { FunTableFilterPipe } from './pipes/fun-table-filter.pipe';
import { FunChartComponent } from './fun-chart/fun-chart.component';
import { ChartModule } from 'angular-highcharts';
import { FunMetricChartComponent } from './fun-metric-chart/fun-metric-chart.component';
import { AngularFontAwesomeModule } from 'angular-font-awesome';
import { FormsModule } from '@angular/forms';
import { SafeHtmlPipe } from './pipes/safe-html.pipe';
import { Angular2FontawesomeModule } from 'angular2-fontawesome/angular2-fontawesome'
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { AngularCollapseModule } from 'angular-collapse';
import { CreateChartComponent } from './performance/create-chart/create-chart.component';
import { PreviewFunMetricComponent } from './fun-metric-chart/preview-fun-metric.component';
import { ScrollToDirective } from './scroll-to.directive';
import { RegressionComponent } from './regression/regression.component';
import { FunSpinnerComponent } from './fun-spinner/fun-spinner.component';
import { SubmitJobComponent } from './regression/submit-job/submit-job.component';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { SuiteDetailComponent } from './regression/suite-detail/suite-detail.component';
import { CancelBtnLinkComponent } from "./cancel-btn-link/cancel-btn-link.component";
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { SiteConstructionComponent } from './site-construction/site-construction.component'
import { RegressionAdminComponent } from './regression/regression-admin/regression-admin.component';
import { JiraInfoComponent } from './jira-info/jira-info.component';
import { RegressionSummaryComponent } from './regression/regression-summary/regression-summary.component';
import { RegressionSummaryChartComponent } from './regression/regression-summary/regression-summary-chart/regression-summary-chart.component';
import { ScriptHistoryComponent } from './regression/script-history/script-history.component';
import { SummaryJiraInfoComponent } from "./jira-info/summary-jira-info.component";
import { ScriptSelectorComponent } from './regression/script-selector/script-selector.component';
import { NotFoundComponent } from './not-found/not-found.component';
import { ReRunPanelComponent } from './regression/re-run-panel/re-run-panel.component';
import { AlertsComponent } from './alerts/alerts.component';
import { SchedulerAdminComponent } from './scheduler-admin/scheduler-admin.component';
import { ToasterModule, ToasterService } from "angular2-toaster";
import { LogViewerComponent } from './log-viewer/log-viewer.component';
import { SmartLabelComponent } from './smart-label/smart-label.component';
import {QueueViewerComponent} from "./regression/queue-viewer/queue-viewer.component";
import { TriageComponent } from './triage/triage.component';
import { SectionHorizontalLineComponent} from "./ui-elements/section-horizontal-line/section-horizontal-line.component";
import { ReactiveFormsModule } from '@angular/forms';
import { UserComponent } from './user/user.component';
import { TestBedComponent } from './regression/test-bed/test-bed.component';
import { JirasComponent } from './regression/jiras/jiras.component';
import { JobSpecComponent } from './regression/job-spec/job-spec.component';
import { JsonInputComponent } from './ui-elements/json-input/json-input.component';
import { Triage2Component } from './regression/triage2/triage2.component';
import { JenkinsFormComponent } from './jenkins-form/jenkins-form.component';
import { TriageDetailComponent } from './regression/triage2/triage-detail/triage-detail.component';
import { SmartButtonComponent } from './ui-elements/smart-button/smart-button.component';
import { AdminComponent } from "./performance/admin/admin.component";
import { ScoresTableComponent } from './performance/scores-table/scores-table.component';
import { PerformanceTableComponent } from './performance/performance-table/performance-table.component';
import { AdminDagComponent } from './performance/admin/admin-dag/admin-dag.component';

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    PerformanceComponent,
    FunTableComponent,
    TestComponent,
    FunTableFilterPipe,
    FunChartComponent,
    FunMetricChartComponent,
    SafeHtmlPipe,
    CreateChartComponent,
    PreviewFunMetricComponent,
    ScrollToDirective,
    RegressionComponent,
    FunSpinnerComponent,
    SubmitJobComponent,
    SuiteDetailComponent,
    CancelBtnLinkComponent,
    SiteConstructionComponent,
    RegressionAdminComponent,
    JiraInfoComponent,
    RegressionSummaryComponent,
    TriageComponent,
    RegressionSummaryChartComponent,
    ScriptHistoryComponent,
    SummaryJiraInfoComponent,
    ScriptSelectorComponent,
    NotFoundComponent,
    ReRunPanelComponent,
    AlertsComponent,
    SchedulerAdminComponent,
    LogViewerComponent,
    SmartLabelComponent,
    QueueViewerComponent,
    SectionHorizontalLineComponent,
    UserComponent,
    TestBedComponent,
    JirasComponent,
    JobSpecComponent,
    JsonInputComponent,
    Triage2Component,
    JenkinsFormComponent,
    TriageDetailComponent,
    SmartButtonComponent,
    AdminComponent,
    ScoresTableComponent,
    PerformanceTableComponent,
    AdminDagComponent
  ],
  imports: [
    BsDropdownModule,
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    MatSortModule,
    ChartModule,
    AngularFontAwesomeModule,
    FormsModule,
    Angular2FontawesomeModule,
    AngularCollapseModule,
    NgMultiSelectDropDownModule,
    ReactiveFormsModule,
    NgbModule,
    NgbTooltipModule,
    ToasterModule.forRoot()
  ],

  providers: [ApiService, LoggerService],
  bootstrap: [AppComponent]
})
export class AppModule {
}
