import { Component, OnInit } from '@angular/core';
import { PerformanceComponent } from "../performance/performance.component";

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  testClose: boolean = true;
  x: number = 20;
  y: number = 30;

  constructor() { }

  ngOnInit() {
  }

  buttonClose(x, y): void{
    this.testClose = !this.testClose;
    let sum = x + y;
    console.log(sum);
  }
}
