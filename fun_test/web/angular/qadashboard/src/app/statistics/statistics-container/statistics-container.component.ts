import {Component, Input, OnChanges, OnInit} from '@angular/core';

@Component({
  selector: 'app-statistics-container',
  templateUrl: './statistics-container.component.html',
  styleUrls: ['./statistics-container.component.css']
})
export class StatisticsContainerComponent implements OnInit, OnChanges {
  @Input() statistics: any [];  // {statisticsCategory: , statisticsSubCategory:}
  @Input() scriptExecutionInfo: any = null;
  constructor() { }

  ngOnInit() {
  }

  ngOnChanges() {
    console.log(this.statistics);
    // fetch data using suite_execution_id
  }

}
