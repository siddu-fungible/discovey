import {Component, Input, OnInit} from '@angular/core';
import {slideInOutAnimation,showAnimation} from "../../animations/generic-animations";

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

  constructor() { }

  ngOnInit() {
    this.title = this.data.title;
    this.xAxisLabel = this.data.xAxisLabel;
    this.y1AxisLabel = this.data.y1AxisLabel;
    this.y1Values = this.data.y1Values;
    this.xValues = this.data.xValues;
  }

  showTables(): void {
    this.showTable = !this.showTable;
  }
}
