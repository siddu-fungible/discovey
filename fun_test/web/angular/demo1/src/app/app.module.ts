import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
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
import { FunTableFilterPipe } from './pipes/fun-table-filter.pipe';
import { FunChartComponent } from './fun-chart/fun-chart.component';
import { ChartModule } from 'angular-highcharts';
import { FunMetricChartComponent } from './fun-metric-chart/fun-metric-chart.component';
import { AngularFontAwesomeModule } from 'angular-font-awesome';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import { SafeHtmlPipe } from './pipes/safe-html.pipe';
import { Angular2FontawesomeModule } from 'angular2-fontawesome/angular2-fontawesome'
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { AngularCollapseModule } from 'angular-collapse';
import { Demo1Component } from './demo1/demo1.component';
import { DpusComponent } from './dpus/dpus.component';
// import { CreateChartComponent } from './create-chart/create-chart.component';
import {
  MatAutocompleteModule,
  MatBadgeModule,
  MatBottomSheetModule,
  MatButtonModule,
  MatButtonToggleModule,
  MatCardModule,
  MatCheckboxModule,
  MatChipsModule,
  MatDatepickerModule,
  MatDialogModule,
  MatDividerModule,
  MatExpansionModule,
  MatGridListModule,
  MatIconModule,
  MatInputModule,
  MatListModule,
  MatMenuModule,
  MatNativeDateModule,
  MatPaginatorModule,
  MatProgressBarModule,
  MatProgressSpinnerModule,
  MatRadioModule,
  MatRippleModule,
  MatSelectModule,
  MatSidenavModule,
  MatSliderModule,
  MatSlideToggleModule,
  MatSnackBarModule,
  MatSortModule,
  MatStepperModule,
  MatTableModule,
  MatTabsModule,
  MatToolbarModule,
  MatTooltipModule,
  MatTreeModule,
} from '@angular/material';


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
    Demo1Component,
    DpusComponent
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
    ReactiveFormsModule,
    Angular2FontawesomeModule,  // Add this line
    AngularCollapseModule,
      MatAutocompleteModule,
  MatBadgeModule,
  MatBottomSheetModule,
  MatButtonModule,
  MatButtonToggleModule,
  MatCardModule,
  MatCheckboxModule,
  MatChipsModule,
  MatDatepickerModule,
  MatDialogModule,
  MatDividerModule,
  MatExpansionModule,
  MatGridListModule,
  MatIconModule,
  MatInputModule,
  MatListModule,
  MatMenuModule,
  MatNativeDateModule,
  MatPaginatorModule,
  MatProgressBarModule,
  MatProgressSpinnerModule,
  MatRadioModule,
  MatRippleModule,
  MatSelectModule,
  MatSidenavModule,
  MatSliderModule,
  MatSlideToggleModule,
  MatSnackBarModule,
  MatSortModule,
  MatStepperModule,
  MatTableModule,
  MatTabsModule,
  MatToolbarModule,
  MatTooltipModule,
  MatTreeModule,
  ],
  exports: [
        MatAutocompleteModule,
    MatBadgeModule,
    MatBottomSheetModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatStepperModule,
    MatDatepickerModule,
    MatDialogModule,
    MatDividerModule,
    MatExpansionModule,
    MatGridListModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatMenuModule,
    MatNativeDateModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatRadioModule,
    MatRippleModule,
    MatSelectModule,
    MatSidenavModule,
    MatSliderModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatSortModule,
    MatTableModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    MatTreeModule,
  ],

  providers: [ApiService, LoggerService],
  bootstrap: [AppComponent]
})
export class AppModule {
}
