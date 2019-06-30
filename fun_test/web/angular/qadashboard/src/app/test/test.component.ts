import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {from, Observable, of} from "rxjs";
import {mergeMap, switchMap} from "rxjs/operators";
import { CommonService } from "../services/common/common.service";

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
  myDict: any = {};


  tooltipContent = "";

  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService) {
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
    // let modules = ['networking','storage'];
    // for (let module of modules){
    //   this.payload['module'] = module;
    // }
    //
    // new Observable(observer => {
    //   observer.next(true);
    //   observer.complete();
    //   return () => {}
    // }).pipe(switchMap(response => {
    //   return this.test({module: 'networking'});
    //   }),
    //   switchMap(response => {
    //     return this.test({module: 'storage'});
    //   }),
    //   switchMap(response => {
    //     this.donePopulation = true;
    //     return of(null);
    //   })).subscribe(response => {}, error => {
    // });

    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {}
    }).pipe(switchMap(response => {
      //console.log(response);
      let numbers = [];
      this.initialFilterData.map(filter => {numbers.push(numbers.length)});
      return from(numbers).pipe(
          mergeMap(filterIndex => this.test(filterIndex)));
    })).subscribe(response => {}, error => {
    });
  }

  //initialFilterData[filterIndex].payload





  test(index: any): any{
    console.log('beginning test');
    let today = new Date();
    let payload = this.initialFilterData[index].payload;
      return this.apiService.post("/regression/get_test_case_executions_by_time" + "?days_in_past=5", payload).pipe(switchMap((response) => {
      for (let i in response.data) {
        let historyTime = new Date(this.commonService.convertToLocalTimezone(response.data[i].started_time)); //.replace(/\s+/g, 'T')); // For Safari
        //console.log(historyTime + " " + today);
        //console.log('inside loop');

        if (this.commonService.isSameDay(historyTime, today)){
          if (this.myDict[response.data[i].test_case_id] != response.data[i].script_path){
            this.myDict[response.data[i].test_case_id].push(response.data[i].script_path);
            if (response.data[i].result == 'FAILED') {
              ++this.numFailed;
              //console.log(payload.module + " fails " + this.numFailed);
            }
            else if (response.data[i].result == 'PASSED'){
              ++this.numPassed
              //console.log(payload.module + " passes " + this.numPassed);
            }
            else if (response.data[i].result == 'NOT_RUN'){
              ++this.numNotRun;
              //console.log(payload.module + " not run: " + this.numNotRun);
            }
            else if (response.data[i].result == 'IN_PROGRESS'){
              ++this.numInProgress;
            }
          //console.log(payload.module  + " " + response.data[i].started_time + ' ' + response.data[i].suite_execution_id);

          }
          else{
            console.log('Detected duplicate: ' + response.data[i].test_case_id + ' ' + response.data[i].sript_path);
          }
        }

      }
      //console.log('Inside request: ' + payload['module'] + ' num passed: ' + this.numPassed + ' num failed: ' + this.numFailed);
      this.populateResults();
      this.numPassed = this.numFailed = this.numNotRun = 0;
      return of(true);
    }));
  }

  populateResults() {
      console.log('populating results');
      this.y1Values[0].data.push(this.numPassed);
      this.y1Values[1].data.push(this.numFailed);
      this.y1Values[2].data.push(this.numNotRun);
      //this.donePopulation = true;
      this.y1Values = [...this.y1Values];
      console.log('end populate results');




  }





}


