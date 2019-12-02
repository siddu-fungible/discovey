import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegisteredAsset} from "../../../regression/definitions";
import {RegressionService} from "../../../regression/regression.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";

@Component({
  selector: 'app-vp-utilization',
  templateUrl: './vp-utilization.component.html',
  styleUrls: ['./vp-utilization.component.css']
})
export class VpUtilizationComponent implements OnInit, OnChanges {
  @Input() scriptExecutionInfo: any = null;
  @Input() selectedAsset: RegisteredAsset = null;
  data: any = null;
  parsedData: any = {};
  driver: any = null;
  suiteExecutionId: number;
  constructor(private regressionService: RegressionService, private loggerService: LoggerService) {
    this.driver = of(true).pipe(switchMap(response => {
     return this.regressionService.testCaseTimeSeries(this.suiteExecutionId,
       null,
       null,
       null,
       null,
       100,
       1050, this.selectedAsset.asset_id);

    })).pipe(switchMap(response => {
      this.data = response;
      this.parseData(this.data);
      return of(true);
    }));

  }

  parseData(data) {

  }

  ngOnInit() {
  }

  ngOnChanges() {
    if (this.scriptExecutionInfo && this.scriptExecutionInfo.suite_execution_id) {
      this.suiteExecutionId = this.scriptExecutionInfo.suite_execution_id;
      this.driver.subscribe(response => {

      }, error => {
        this.loggerService.error("Unable to fetch data");
      })
    }
  }

}
