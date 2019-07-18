import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {from, Observable, of} from "rxjs";
import {mergeMap, switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {RegressionService} from "../../regression/regression.service";

@Component({
  selector: 'app-smoke-test-storage-widget',
  templateUrl: './smoke-test-storage-widget.component.html',
  styleUrls: ['./smoke-test-storage-widget.component.css']
})
export class SmokeTestStorageWidgetComponent implements OnInit {

  items: any;
  numList: number[] = [6,1,9];
  lastTwoTestSuites: any[] = [];
  lastTwoResults: string[] = [];
  passed: number = 4;
  failed: number = 0;
  result: string;
  isDone: boolean = false;
  numbers: number[] = [0,1];
  myTitle: string = "My Title";
  mySubtitle: string = "My Subtitle";


  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService, private regressionService: RegressionService) {
  }


  stateMap = this.regressionService.stateMap;
  stateStringMap = this.regressionService.stateStringMap;
  ngOnInit() {

    console.log(this.stateMap);
    console.log(this.stateStringMap);

    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(switchMap(response => {
      return this.fetchData();
    })).subscribe(response => {
    }, error => {
      this.logger.error('Failed to fetch data');
    });

  }


  fetchData() {
    let stateFilter = 'ALL';
    let count = 0;
    //completed (passed or failed), killed, aborted (override result w/ failed) --> done
    //only care about result when completed
    //separate icon for in progress
    //use field result
    //get result of past 2 suites
    //display date + result of previous test
    //statemap, statestringmap (in regression service)
    //scheduler_global.py, suite-detail.component
    let payload = {tags: '["smoke"]', tag: "smoke"};
    return this.apiService.post("/regression/suite_executions/" + 10 + "/" + 1 + "/" + stateFilter, payload).pipe(switchMap(response => {
      for (let i of response.data) {
        if (this.lastTwoResults.length == 2) {
          break;
        }


        if (i.fields.state == this.stateMap.AUTO_SCHEDULED) {
        } else if (i.fields.state == this.stateMap.COMPLETED) {
          this.lastTwoResults.push(i.fields.result);
          this.lastTwoTestSuites.push(i)

        } else if (i.fields.state < this.stateMap.COMPLETED) {
          this.lastTwoResults.push('FAILED');
          this.lastTwoTestSuites.push(i);
        } else {
          this.lastTwoResults.push('IN_PROGRESS');
          this.lastTwoTestSuites.push(i);
        }

      }
      this.isDone = true;
      return of(true);
    }));
  }

   trimTime(t) {
    return this.regressionService.getPrettyLocalizeTime(t);
  }
}
