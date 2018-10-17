import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardComponent }   from './dashboard/dashboard.component';
import { PerformanceComponent } from "./performance/performance.component";
import {TestComponent} from "./test/test.component";
import {FunMetricChartComponent} from "./fun-metric-chart/fun-metric-chart.component";
import {Demo1Component} from "./demo1/demo1.component";
import {RegressionComponent} from "./regression/regression.component";

const routes: Routes = [
  { path: 'upgrade', component: DashboardComponent },
  { path: 'upgrade/dashboard', component: DashboardComponent },
  { path: 'upgrade/performance', component: PerformanceComponent },
  { path: 'upgrade/regression', component: RegressionComponent },
  { path: 'upgrade/performance/atomic/:id', component: FunMetricChartComponent},
  { path: 'upgrade/test', component: TestComponent },
  { path: 'upgrade/demo1', component: Demo1Component }
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ]
})
export class AppRoutingModule {}


