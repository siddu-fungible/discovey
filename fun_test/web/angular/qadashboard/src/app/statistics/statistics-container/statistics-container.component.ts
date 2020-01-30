import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegisteredAsset} from "../../regression/definitions";

@Component({
  selector: 'app-statistics-container',
  templateUrl: './statistics-container.component.html',
  styleUrls: ['./statistics-container.component.css']
})
export class StatisticsContainerComponent implements OnInit, OnChanges {
  @Input() statistics: any [];  // {statisticsCategory: , statisticsSubCategory:}
  @Input() scriptExecutionInfo: any = null;
  selectedAsset: RegisteredAsset = null;
  constructor() { }

  ngOnInit() {
  }

  ngOnChanges() {
    console.log(this.statistics);
    // fetch data using suite_execution_id
    if (this.scriptExecutionInfo) {
      let suiteExecutionId = this.scriptExecutionInfo.suite_execution_id;
      console.log(suiteExecutionId);

      if (this.scriptExecutionInfo.hasOwnProperty('registered_assets')) {
        if (this.scriptExecutionInfo.registered_assets.length > 0) {
          this.selectedAsset = this.scriptExecutionInfo.registered_assets[0];
        }
      }
    }
  }

}
