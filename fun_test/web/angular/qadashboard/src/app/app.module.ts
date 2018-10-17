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
import { Demo1Component } from './demo1/demo1.component';
import { CreateChartComponent } from './create-chart/create-chart.component';
import { PreviewFunMetricComponent } from './fun-metric-chart/preview-fun-metric.component';
import { ScrollToDirective } from './scroll-to.directive';
import { RegressionComponent } from './regression/regression.component';

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
    Demo1Component,
    PreviewFunMetricComponent,
    ScrollToDirective,
    RegressionComponent
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
    Angular2FontawesomeModule,  // Add this line
    AngularCollapseModule,
  ],

  providers: [ApiService, LoggerService],
  bootstrap: [AppComponent]
})
export class AppModule {
}
