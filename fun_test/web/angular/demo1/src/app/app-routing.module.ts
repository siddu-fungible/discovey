import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';

import {DashboardComponent} from './dashboard/dashboard.component';
import {TestComponent} from "./test/test.component";
import {FunMetricChartComponent} from "./fun-metric-chart/fun-metric-chart.component";
import {Demo1Component} from "./demo1/demo1.component";
import {DpusComponent} from "./dpus/dpus.component";
import {AppComponent} from "./app.component";
import {PoolsComponent} from "./workflows/pools/pools.component";

const routes: Routes = [
  {
    path: 'demo/demo1', component: Demo1Component, children: [
      {path: 'dpus', component: DpusComponent},
      {path: 'pools', component: PoolsComponent}
    ]
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}


