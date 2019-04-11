import { Component, OnInit } from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";


@Component({
  selector: 'app-test-bed',
  templateUrl: './test-bed.component.html',
  styleUrls: ['./test-bed.component.css']
})
export class TestBedComponent implements OnInit {

  testBeds: any [] = null;
  automationStatus = {};
  constructor(private regressionService: RegressionService) { }

  ngOnInit() {
    // fetchUsers
    // fetchTestbeds
    let o = new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      };
    }).pipe(
      switchMap(response => {
          return this.fetchTestBeds();
      }),
      switchMap(response => {
        return this.fetchAutomationStatus();
      }));

    o.subscribe();
  }

  fetchTestBeds() {
    return this.regressionService.fetchTestbeds().pipe(switchMap(response => {
      this.testBeds = response;
      return of(this.testBeds);
    }))
  }

  fetchAutomationStatus() {
    return forkJoin(...this.testBeds.map((testBed) => {
      return this.regressionService.testBedInProgress(testBed.name).pipe(switchMap(response => {
        this.automationStatus[testBed.name] = {numExecutions: 0, executionId: -1};
        if (response) {
          let numExecutions = response.length;
          let executionId = numExecutions;
          if (numExecutions > 0) {
            executionId = response[0].execution_id
          }
          this.automationStatus[testBed.name] = {numExecutions: numExecutions, executionId: executionId}
        }
        this.automationStatus[testBed] = response;
          return of(null);
        }))
      })
    )
  }


}
