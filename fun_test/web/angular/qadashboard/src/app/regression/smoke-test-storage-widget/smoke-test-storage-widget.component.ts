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
  styleUrls: ['./smoke-test-storage-widget.component.css']
})
export class SmokeTestStorageWidgetComponent implements OnInit {

  lastTwoSuites: Suite[] = [];
  isDone: boolean = false;
  numbers: number[] = [0, 1];
  myURL: string = "<a href = 'http://www.youtube.com'>F1 storage smoke test</a>";


  iconDict: any = {
    'PASSED': "<img  src='http://jenkins-hw-01:8080/static/d3af0992/images/32x32/health-80plus.png'>",
    'FAILED': "<img src='http://jenkins-hw-01:8080/static/d3af0992/images/32x32/health-00to19.png'>",
    'IN_PROGRESS': "<img src='http://jenkins-hw-01:8080/static/d3af0992/images/32x32/health-60to79.png'>"
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
    return this.apiService.post("/regression/suite_executions/" + 10 + "/" + 1 + "/" + stateFilter, payload).pipe(switchMap(response => {
      for (let i of response.data) {
        let mySuite = new Suite();
        if (this.lastTwoSuites.length == 2) {
          break;
        }
        if (i.fields.state == this.stateMap.AUTO_SCHEDULED) {
          continue;
        } else if (i.fields.state == this.stateMap.COMPLETED) {
          mySuite.result = i.fields.result;
          mySuite.time = this.trimTime(i.fields.completed_time);

        } else if (i.fields.state < this.stateMap.COMPLETED) {
          mySuite.result = 'FAILED';
          mySuite.time = this.trimTime(i.fields.completed_time);
        } else {
          mySuite.result = 'IN_PROGRESS'
          mySuite.time = this.trimTime(i.fields.scheduled_time);
        }
        mySuite.numFailed = i.num_failed;
        mySuite.numPassed = i.num_passed;
        this.lastTwoSuites.push(mySuite);

      }
      this.isDone = true;
      return of(true);
    }));
  }

  trimTime(t) {
    return this.regressionService.getPrettyLocalizeTime(t);
  }
}
