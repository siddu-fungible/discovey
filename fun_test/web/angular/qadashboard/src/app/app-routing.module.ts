import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardComponent }   from './dashboard/dashboard.component';
import { PerformanceComponent } from "./performance/performance.component";

const routes: Routes = [
  { path: 'upgrade', component: DashboardComponent},
  { path: 'upgrade/dashboard', component: DashboardComponent },
  { path: 'upgrade/performance', component: PerformanceComponent }
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ]
})
export class AppRoutingModule {}


