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
import {ApiService} from "./services/api/api.service";
import {LoggerService} from "./services/logger/logger.service";
import { TestComponent } from './test/test.component';
import { FunTableFilterPipe } from './pipe/fun-table-filter.pipe';
import { ChartModule } from 'angular-highcharts';
import { ChartComponent } from './chart/chart.component';
import { FunChartComponent } from './fun-chart/fun-chart.component';


@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    PerformanceComponent,
    FunTableComponent,
    TestComponent,
    FunTableFilterPipe,
    ChartComponent,
    FunChartComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    MatSortModule,
    ChartModule
  ],

  providers: [ApiService, LoggerService],
  bootstrap: [AppComponent]
})
export class AppModule {
}
