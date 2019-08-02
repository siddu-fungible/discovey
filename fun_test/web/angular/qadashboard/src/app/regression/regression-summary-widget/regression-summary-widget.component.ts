import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {from, Observable, of} from "rxjs";
import {mergeMap, switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";

@Component({
  selector: 'app-regression-summary-widget',
  templateUrl: './regression-summary-widget.component.html',
  styleUrls: ['./regression-summary-widget.component.css']
})
export class RegressionSummaryWidgetComponent implements OnInit {

  initialFilterData = [{info: "Networking overall", payload: {module: "networking"}}, {
    info: "Storage overall",
    payload: {module: "storage"}
  }, {
    info: "Networking sanity", payload: {module: "networking", test_case_execution_tags: ["networking-sanity"]}
  }
  ];

  y1Values: any = [];
  payload: any = {};
  x1Values: string[] = ['Networking overall', 'Storage overall', 'Networking sanity'];
  clickUrls: any = {};
  numInProgress: number = 0;

  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService) {
  }

  initializeY1Values() {
    this.y1Values = [{
      name: 'Passed',
      data: Array(this.x1Values.length).fill(0),
      color: 'green'
    }
      , {
        name: 'Failed',
        data: Array(this.x1Values.length).fill(0),
        color: 'red'

      }, {
        name: 'Not-run',
        data: Array(this.x1Values.length).fill(0),
        color: 'grey'

      },
      {
        name: 'In-progress',
        data: Array(this.x1Values.length).fill(0),
        color: '#ffc200'
      }

    ];
  }

  ngOnInit() {

    this.initializeY1Values();

    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(switchMap(response => {
      let numbers = [];
      this.initialFilterData.map(filter => {
        numbers.push(numbers.length)
      });
      return from(numbers).pipe(
        mergeMap(filterIndex => this.fetchTestCaseExecutions(filterIndex)));
    })).subscribe(response => {
    }, error => {
      this.logger.error('Failed to fetch test case executions');
    });
  }

  fetchTestCaseExecutions(index: number): any {
    let numPassed = 0;
    let numFailed = 0;
    let numNotRun = 0;
    let numInProgress = 0;
    let today = new Date();
    let payload = this.initialFilterData[index].payload;
    this.clickUrls[this.initialFilterData[index].info] =  "/regression/summary";
    return this.apiService.post("/regression/get_test_case_executions_by_time" + "?days_in_past=1", payload).pipe(switchMap((response) => {
      for (let i in response.data) {
        let historyTime = new Date(this.commonService.convertToLocalTimezone(response.data[i].started_time));
        if (this.commonService.isSameDay(historyTime, today) && !response.data[i].is_re_run) {
          if (response.data[i].result == 'FAILED') {
            ++numFailed;
          } else if (response.data[i].result == 'PASSED') {
            ++numPassed
          } else if (response.data[i].result == 'NOT_RUN') {
            ++numNotRun;
          } else if (response.data[i].result == 'IN_PROGRESS') {
            ++numInProgress;
          }
        }
      }
      this.populateResults(index, numPassed, numFailed, numNotRun, numInProgress);
      return of(true);
    }));
  }

  populateResults(index, numPassed, numFailed, numNotRun, numInProgress) {
    this.y1Values[0].data[index] = numPassed; //make these local vars, pass to populateResults
    this.y1Values[1].data[index] = numFailed;
    this.y1Values[2].data[index] = numNotRun;
    this.y1Values[3].data[index] = numInProgress;
    this.y1Values = [...this.y1Values];
  }
}

