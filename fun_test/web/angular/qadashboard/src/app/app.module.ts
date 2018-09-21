import {BrowserModule} from '@angular/platform-browser';
import {NgModule} from '@angular/core';

import {AppComponent} from './app.component';
import {DashboardComponent} from './dashboard/dashboard.component';
import {AppRoutingModule} from './app-routing.module';
import {PerformanceComponent} from './performance/performance.component';
import {HttpClientModule} from '@angular/common/http';
import {ApiService} from "./services/api/api.service";
import {LoggerService} from "./services/logger/logger.service";
import { TestComponent } from './test/test.component';


@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    PerformanceComponent,
    TestComponent

  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule
  ],

  providers: [ApiService, LoggerService],
  bootstrap: [AppComponent]
})
export class AppModule {
}
