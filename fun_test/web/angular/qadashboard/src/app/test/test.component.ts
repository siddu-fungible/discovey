import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})
export class TestComponent implements OnInit {
  yValues: any = [];
  xValues: any = [];
  title: string;
  xAxisLabel: string;
  yAxisLabel: string;

  constructor() { }

  ngOnInit() {
    // let temp = [];
    // temp["name"] = 'series 1';
    // temp["data"] = [1,2,3,4,5];
    // this.yValues[0] = temp;
    this.yValues.push({ name: 'series 1', data: [1,2,3,4,5]});
    this.yValues.push({ name: 'series 2', data: [6,7,8,9,10]});
    this.yValues.push({ name: 'series 3', data: [11,12,13,14,15]});
    this.yValues.push({ name: 'series 4', data: [16,17,18,19,20]});
    this.yValues.push({ name: 'series 5', data: [21,22,23,24,25]});
    this.xValues.push([0,1,2,3,4]);
    this.title = "Funchart";
    this.xAxisLabel = "Date";
    this.yAxisLabel = "Range";
  }

}
