import {Component, Input, OnChanges, OnInit} from '@angular/core';

@Component({
  selector: 'app-statistics-container',
  templateUrl: './statistics-container.component.html',
  styleUrls: ['./statistics-container.component.css']
})
export class StatisticsContainerComponent implements OnInit, OnChanges {
  @Input() statistics: any [];  // {statisticsCategory: , statisticsSubCategory:}
  constructor() { }

  ngOnInit() {
  }

  ngOnChanges() {
    console.log(this.statistics);
  }

}
