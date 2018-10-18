import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';

import {DashboardComponent} from './dashboard/dashboard.component';
import {TestComponent} from "./test/test.component";
import {FunMetricChartComponent} from "./fun-metric-chart/fun-metric-chart.component";
import {Demo1Component} from "./demo1/demo1.component";
import {DpusComponent} from "./dpus/dpus.component";
import {AppComponent} from "./app.component";
import {PoolsComponent} from "./workflows/pools/pools.component";
import {VolumesComponent} from "./workflows/volumes/volumes.component";
import {VolumeComponent} from "./volume/volume.component";
import {DpuComponent} from "./dpu/dpu.component";
import {PoolComponent} from "./pool/pool.component";

const routes: Routes = [
  {
    path: 'demo/demo1', component: Demo1Component, children: [
      {path: 'dpus', component: DpusComponent},
      {path: 'pools', component: PoolsComponent},
      {path: 'pool/:name', component: PoolComponent},
      {path: 'volumes', component: VolumesComponent},
      {path: 'volume/:name', component: VolumeComponent},
      {path: 'dpu/:name', component: DpuComponent}
    ]
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}


