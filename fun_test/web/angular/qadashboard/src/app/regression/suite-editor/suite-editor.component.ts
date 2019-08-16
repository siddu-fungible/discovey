import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup, Validators} from "@angular/forms";
import {TestBedService} from "../test-bed/test-bed.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";

class SuiteEntry {
  path: string;
  test_case_ids: number[] = null;
  inputs: any = null
}
enum CustomDutSelection {  // used by the Custom test-bed spec modal
  NUM_DUTS,
  SPECIFIC_DUTS
}

@Component({
  selector: 'app-suite-editor',
  templateUrl: './suite-editor.component.html',
  styleUrls: ['./suite-editor.component.css']
})
export class SuiteEditorComponent implements OnInit {
  testCaseIds: number[] = null;
  inputs: any = null;
  customTestBedSpec: any = null;
  addingCustomTestBedSpec: boolean = true;
  inputsExample: string = '{"abc":123}';
  testBeds: any = null;
  selectedTestBed: any = null;
  assets: any = null;
  dutAssets: any = [];
  hostAssets: any = [];
  perfListenerAssets: any = [];
  selectedDutAsset: any = null;
  numDuts: number = -1;
  CustomDutSelection = CustomDutSelection;
  MAX_NUM_DUTS = 10;
  newSuiteEntryForm = new FormGroup({
    path: new FormControl(''),
    testCaseIds: new FormControl(''),
    inputs: new FormControl('')
  });

  customTestBedSpecForm = new FormGroup({
    customDutSelection: new FormControl(),
    selectedTestBed: new FormControl(),
    numDuts: new FormControl('', [Validators.max(10)])
  });

  constructor(private testBedService: TestBedService) {

  }

  ngOnInit() {
    new Observable(observer => {
      observer.next(true);
      return () => {

      }
    }).pipe(switchMap((response) => {
      return this.testBedService.testBeds();
    })).pipe(switchMap(response => {
      this.testBeds = response;
      return this.testBedService.assets();
    })).pipe(switchMap(response => {
      this.assets = response;
      this.assets.forEach((asset) => {
        if (asset.type === 'DUT') {
          this.dutAssets.push(asset);
        }
        if (asset.type === 'Host') {
          this.hostAssets.push(asset)
        }
        if (asset.type === 'Perf Listener') {
          this.perfListenerAssets.push(asset);
        }

      });

      return of(true);
    })).subscribe();

    this.customTestBedSpecForm.get('customDutSelection').valueChanges.subscribe(selection => {
      if (selection == CustomDutSelection.SPECIFIC_DUTS.toString()) {
        this.customTestBedSpecForm.get('numDuts').disable();
      } else {
        this.customTestBedSpecForm.get('numDuts').enable();

      }
    })
  }

  testCaseIdsChanged(testCaseIds) {
    this.testCaseIds = testCaseIds;
  }

  inputsChanged(inputs) {
    this.inputs = inputs;
  }

  customTestBedSpecChanged(customTestBedSpec) {
    this.customTestBedSpec = customTestBedSpec;
  }

  test() {
    //console.log(this.selectedTestBed);
    console.log(this.customTestBedSpecForm.get("selectedTestBed").value);
    console.log(this.customTestBedSpecForm.get("customDutSelection").value);
        console.log(this.customTestBedSpecForm.get("numDuts").value);
        console.log(this.customTestBedSpecForm.get("numDuts").valid);

  }
}
