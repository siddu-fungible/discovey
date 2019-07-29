import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {from, Observable, of} from "rxjs";
import {mergeMap, switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {RegressionService} from "../../regression/regression.service";


class Suite {
  result: string;
  time: string;
  numPassed: number;
  numFailed: number;
}

@Component({
  selector: 'app-smoke-test-storage-widget',
  templateUrl: './smoke-test-storage-widget.component.html',
  styleUrls: ['./smoke-test-storage-widget.component.css'],
})
export class SmokeTestStorageWidgetComponent implements OnInit {

  lastTwoSuites: Suite[] = [];
  isDone: boolean = false;
  numbers: number[] = [0, 1];
  iconDict: any = {
    'PASSED': "/static/media/sun_icon.png",
    'FAILED': "/static/media/storm_icon.png",
    'IN_PROGRESS': "/static/media/loading_bars.gif"
  };


  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService, private regressionService: RegressionService) {

  }


  stateMap = this.regressionService.stateMap;
  stateStringMap = this.regressionService.stateStringMap;

  ngOnInit() {

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
    let payload = {tags: '["smoke"]', tag: "smoke"};
    let recordsPerPage = 10;
    let pages = 1;
    return this.apiService.post("/regression/suite_executions/" + recordsPerPage + "/" + pages + "/" + stateFilter, payload).pipe(switchMap(response => {
      for (let i of response.data) {
        let suite = new Suite();
        if (this.lastTwoSuites.length == 2) {
          break;
        }
        if (i.fields.state === this.stateMap.AUTO_SCHEDULED) {
          continue;
        } else if (i.fields.state === this.stateMap.COMPLETED) {
          suite.result = i.fields.result;
          suite.time = this.trimTime(i.fields.completed_time);

        } else if (i.fields.state < this.stateMap.COMPLETED) {
          suite.result = 'FAILED';
          suite.time = this.trimTime(i.fields.completed_time);
        } else {
          suite.result = 'IN_PROGRESS'
          suite.time = this.trimTime(i.fields.scheduled_time);
        }
        suite.numFailed = i.num_failed;
        suite.numPassed = i.num_passed;
        this.lastTwoSuites.push(suite);

      }
      this.isDone = true;
      return of(true);
    }));
  }

  trimTime(t) {
    return this.regressionService.getPrettyLocalizeTime(t);
  }
}

