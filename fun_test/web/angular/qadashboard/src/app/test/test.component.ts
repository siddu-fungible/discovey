import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";

class Node {
  uId: number;  // unique Id
  scriptPath: string;
  pk: number = null;
  childrenIds = null;
  indent: number = 0;
  show: boolean = false;
  expanded: boolean = false;
  leaf: boolean = false;
}

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})
export class TestComponent implements OnInit {


  initialFilterData = [{info: "Networking overall", payload: {module: "networking"}}, {info: "Storage overall", payload: {module: "storage"}}];



  filterEntry: any = null;
  y1Values: any = [];
  payload: any = {};
  x1Values: string[] = ['Networking Overall', 'Storage Overall'];
  failedList: any[] = [];
  passedList: any[] = [];
  notRunList: any[] = [];
  inProgressList: any[] = [];
  mode: string = "date";
  numPassed: number = 0;
  numFailed: number = 0;
  numNotRun: number = 0;
  numInProgress: number = 0;
  donePopulation: boolean = false;


  tooltipContent = "";

  constructor(private apiService: ApiService, private logger: LoggerService, private renderer: Renderer2) {
  }

  initializeY1Values() {
    console.log('initializing y1values');
    this.y1Values = [{
        name: 'Passed',
        data: [],
        color: 'green'
    }
    ,  {
        name: 'Failed',
        data: [],
        color: 'red'

    }, {
        name: 'Not-run',
        data: [],
        color: 'grey'

    }];
  }

  ngOnInit() {
    /*
    this.tooltipContent = this.renderer.createElement("span");
    const text = this.renderer.createText("ABCCCC");
    this.renderer.appendChild(this.tooltipContent, text);
    let s = 0;*/
    this.initializeY1Values();
    let modules = ['networking','storage'];
    for (let module of modules){
      this.payload['module'] = module;
    }

    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {}
    }).pipe(switchMap(response => {
      return this.test({module: 'networking'});
      }),
      switchMap(response => {
        return this.test({module: 'storage'});
      }),
      switchMap(response => {
        this.donePopulation = true;
        return of(null);
      })).subscribe(response => {}, error => {
    });
  }






  test(payload: any): any{
    console.log('beginning test');

      return this.apiService.post("/regression/get_test_case_executions_by_time" + "?days_in_past=3", payload).pipe(switchMap((response) => {
      for (let i in response.data) {
        if (response.data[i].result == 'FAILED') {
          this.numFailed = this.numFailed + 1;
          //console.log("fails " + this.numFailed);
        }
        else if (response.data[i].result == 'PASSED'){
          this.numPassed = this.numPassed + 1;
          //console.log("passes " + this.numPassed);
        }
        else if (response.data[i].result == 'NOT_RUN'){
          this.numNotRun = this.numNotRun + 1;
          //console.log("not run: " + this.numNotRun);
        }
        else{
          ++this.numInProgress;
        }
        //console.log(response.data[i].started_time);

      }
      //console.log('Inside request: ' + payload['module'] + ' num passed: ' + this.numPassed + ' num failed: ' + this.numFailed);
      this.populateResults();

      return of(true);
    }));
  }

  populateResults() {
      // this.numPassed = 4;
      // this.numFailed = 7;
      // this.numNotRun = 3;
      console.log('populating results');
      this.y1Values[0].data.push(this.numPassed);
      this.y1Values[1].data.push(this.numFailed);
      this.y1Values[2].data.push(this.numNotRun);
      this.numPassed = 0;
      this.numFailed = 0;
      this.numNotRun = 0;
      //this.donePopulation = true;
      this.y1Values = [...this.y1Values];
      console.log('end populate results');




  }

}


