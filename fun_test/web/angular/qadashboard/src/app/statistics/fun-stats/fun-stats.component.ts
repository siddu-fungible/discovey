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

  tableHeaders: any[] = [];
  tableData: any[] = [];
  @Input() data: any = {};

  showTable: boolean = false;
  chartReady: boolean = false;
  uniqueTimeStamps: any = new Set();

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
    let y1Values = [];
    let dataByTime = {};
    this.findUniqueTimeStamps(); //find unique timestamps from the series data
    this.xValues = Array.from(this.uniqueTimeStamps.values()).sort();
    this.xValues.forEach(timestamp => {
      dataByTime[timestamp] = [];
    });
    // populating the y values
    for (let series of this.data.collection) {
      let yData = {};
      yData["name"] = series.name;
      this.tableHeaders.push(series.name);
      yData["data"] = [];
      this.xValues.forEach(dateTime => {
        if (series.data.hasOwnProperty(dateTime)) {
          dataByTime[dateTime].push(series.data[dateTime]);
          yData["data"].push(series.data[dateTime]);
        } else {
          dataByTime[dateTime].push("");
          yData["data"].push(null);
        }
      });
      y1Values.push(yData);
    }
    this.y1Values = y1Values;

    // populating the table data
    Object.keys(dataByTime).forEach(date => {
      let temp = [];
      temp.push(date);
      let result = temp.concat(dataByTime[date]);
      this.tableData.push(result);
    });
    this.chartReady = true;
  }

  showTables(): void {
    this.showTable = !this.showTable;
  }

  findUniqueTimeStamps(): void {
    for (let series of this.data.collection) {
      Object.keys(series.data).forEach(dateTime => {
        this.uniqueTimeStamps.add(dateTime);
      });
    }
  }
}
