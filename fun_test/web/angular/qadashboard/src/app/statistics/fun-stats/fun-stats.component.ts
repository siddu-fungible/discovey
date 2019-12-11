import {Component, Input, OnInit} from '@angular/core';
import {slideInOutAnimation, showAnimation} from "../../animations/generic-animations";

@Component({
  selector: 'fun-stats',
  templateUrl: './fun-stats.component.html',
  styleUrls: ['./fun-stats.component.css'],
  animations: [slideInOutAnimation, showAnimation]
})
export class FunStatsComponent implements OnInit {

  title: string = null;
  xAxisLabel: string = null;
  y1AxisLabel: string = null;
  y2AxisLabel: string = null;
  xValues: any = null;
  y1Values: any = null;
  y2Values: any = null;

  @Input() tableHeaders: any[] = [];
  @Input() tableData: any[] = [];
  @Input() data: any = {};

  showTable: boolean = false;
  chartReady: boolean = false;

  constructor() {
  }

  ngOnInit() {
    this.chartReady = false;
    this.tableHeaders = [];
    this.tableHeaders.push("Time");
    this.tableData = [];
    this.title = this.data.name;
    this.xAxisLabel = "Time";
    this.y1AxisLabel = this.data.unit;
    let collection = this.data.collection;
    let y1Values = [];
    let xValues = new Set();
    let tableData = {};
    for (let series of collection) {
      let temp = {};
      temp["name"] = series.name;
      this.tableHeaders.push(series.name);
      temp["data"] = [];
      Object.keys(series.data).forEach(dateTime => {
        if (!xValues.has(dateTime)) {
          xValues.add(dateTime);
          tableData[dateTime] = [];
        }
        tableData[dateTime].push(series.data[dateTime]);
        temp["data"].push(series.data[dateTime]);
      });
      y1Values.push(temp);
    }
    this.y1Values = y1Values;
    this.xValues = Array.from(xValues.values());
    Object.keys(tableData).forEach(date => {
      let temp = [];
      temp.push(date);
      let result = temp.concat(tableData[date]);
      this.tableData.push(result);
    });
    this.chartReady = true;
  }

  showTables(): void {
    this.showTable = !this.showTable;
  }
}
