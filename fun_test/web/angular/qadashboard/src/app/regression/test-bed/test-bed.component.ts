import { Component, OnInit } from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";

enum EditMode {
  NONE = 0,
  MANUAL_LOCK_INITIAL = "Set manual lock",
  MANUAL_LOCK_UPDATE_EXPIRATION = "Update manual lock"
}

@Component({
  selector: 'app-test-bed',
  templateUrl: './test-bed.component.html',
  styleUrls: ['./test-bed.component.css']
})
export class TestBedComponent implements OnInit {

  testBeds: any [] = null;
  automationStatus = {};
  currentEditMode: EditMode = EditMode.NONE;
  EditMode = EditMode;
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
        let numExecutions = -1;
        let executionId = -1;
        let manualLock = false;
        this.automationStatus[testBed.name] = {numExecutions: numExecutions,
          executionId: executionId,
          manualLock: manualLock};
        if (response) {
          let numExecutions = response.length;
          let executionId = numExecutions;
          if (numExecutions > 0) {
            let thisResponse = response[0];
            executionId = thisResponse.execution_id;
            manualLock = thisResponse.manual_lock;
          }
          this.automationStatus[testBed.name] = {numExecutions: numExecutions,
            executionId: executionId,
          manualLock: manualLock}
        }
        this.automationStatus[testBed] = response;
          return of(null);
        }))
      })
    )
  }


}
