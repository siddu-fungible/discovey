import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {from, Observable, of} from "rxjs";
import {mergeMap, switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {RegressionService} from "../../regression/regression.service";

class Suite {
  id: number
  result: string;
  time: string;
  numPassed: number;
  numFailed: number;
}

@Component({
  selector: 'app-network-funcp-sanity-widget',
  templateUrl: './network-funcp-sanity-widget.component.html',
  styleUrls: ['./network-funcp-sanity-widget.component.css']
})
export class NetworkFuncpSanityWidgetComponent implements OnInit {
    lastTwoSuites: Suite[] = [];
  isDone: boolean = false;
  numbers: number[] = [0, 1];
  iconDict: any = {
    'PASSED': "/static/media/sun_icon.png",
    'FAILED': "/static/media/storm_icon.png",
    'IN_PROGRESS': "/static/media/loading_bars.gif"};

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
      }), switchMap(response => {
        return this.fetchTestCaseExecutions(0);
      }), switchMap(response => {
        let temp = this.fetchTestCaseExecutions(1);
        this.isDone = true;
        return temp;

      })).subscribe(response => {

      }, error => {
        this.logger.error('Failed to fetch data');
      }
    );

    console.log(this.lastTwoSuites);
  }




  fetchData() {
    return this.apiService.get("/api/v1/regression/suite_executions/?suite_path=networking_funcp_sanity.json").pipe(switchMap(response => {
      for (let i of response.data) {
        let suite = new Suite();
        if (this.lastTwoSuites.length == 2) {
          break;
        }
        if (i.state === this.stateMap.AUTO_SCHEDULED) {
          continue;
        } else if (i.state === this.stateMap.COMPLETED) {
          suite.result = i.result;
          suite.time = this.trimTime(i.completed_time);

        } else if (i.state < this.stateMap.COMPLETED) {
          suite.result = 'FAILED';
          suite.time = this.trimTime(i.completed_time);
        } else {
          suite.result = 'IN_PROGRESS'
          suite.time = this.trimTime(i.started_time);
        }
        suite.id = i.execution_id;
        this.lastTwoSuites.push(suite);
      }
      //this.isDone = true;
      return of(true);
    }));
  }


  fetchTestCaseExecutions(index) {
    return this.apiService.get(`/api/v1/regression/test_case_executions/?suite_id=${this.lastTwoSuites[index].id}`).pipe(switchMap(response => {
      this.lastTwoSuites[index].numFailed = response.data.num_failed;
      this.lastTwoSuites[index].numPassed = response.data.num_passed;

      return of(true);
    }));
  }

  trimTime(t) {
    return this.regressionService.getPrettyLocalizeTime(t);
  }
}
