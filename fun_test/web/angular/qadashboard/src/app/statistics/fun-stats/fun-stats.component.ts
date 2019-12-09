import {Component, Input, OnInit} from '@angular/core';
import {slideInOutAnimation,showAnimation} from "../../animations/generic-animations";

@Component({
  selector: 'fun-stats',
  templateUrl: './fun-stats.component.html',
  styleUrls: ['./fun-stats.component.css'],
  animations: [slideInOutAnimation, showAnimation]
})
export class FunStatsComponent implements OnInit {

  @Input() title: string = null;
  @Input() xAxisLabel: string = null;
  @Input() y1AxisLabel: string = null;
  @Input() y2AxisLabel: string = null;
  @Input() xValues: any = null;
  @Input() y1Values: any = null;
  @Input() y2Values: any = null;
  @Input() tableHeaders: any[] = [];
  @Input() tableData: any[] = [];

  showTable: boolean = false;


  constructor() { }

  ngOnInit() {
  }

  showTables(): void {
    this.showTable = !this.showTable;
  }
}
