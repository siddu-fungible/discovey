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
enum CustomAssetSelection {  // used by the Custom test-bed spec modal
  NUM,
  SPECIFIC
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


  CustomAssetSelection = CustomAssetSelection;

  MAX_NUM_DUTS = 10;
  MAX_NUM_HOSTS = 20;
  MAX_NUM_PERF_LISTENER_HOSTS = 2;
  dropDownSettings = {};
  assetTypes: any = null;
  assetsByAssetType: any = {};


  newSuiteEntryForm = new FormGroup({
    path: new FormControl(''),
    testCaseIds: new FormControl(''),
    inputs: new FormControl('')
  });

  customTestBedSpecForm = new FormGroup({
    selectedTestBed: new FormControl(),

    customDutSelection: new FormControl(CustomAssetSelection.NUM),
    numDuts: new FormControl('', [Validators.max(this.MAX_NUM_DUTS)]),
    selectedDuts: new FormControl(),

    customHostSelection: new FormControl(CustomAssetSelection.NUM),
    selectedHosts: new FormControl(),
    numHosts: new FormControl('', [Validators.max(this.MAX_NUM_HOSTS)]),

    customPerfListenerHostSelection: new FormControl(CustomAssetSelection.NUM),
    selectedPerfListenerHosts: new FormControl(),
    numPerfListenerHosts: new FormControl('', [Validators.max(this.MAX_NUM_PERF_LISTENER_HOSTS)]),


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
      return this.testBedService.assetTypes();
    })).pipe(switchMap(response => {
      this.assetTypes = response;

      return this.testBedService.assets();
    })).pipe(switchMap(response => {
      this.assets = response;



      return of(true);
    })).subscribe(response => {
      this.prepareFormGroup();
    });




    this.customTestBedSpecForm.get('customDutSelection').valueChanges.subscribe(selection => {
      if (selection == CustomAssetSelection.SPECIFIC.toString()) {
        this.customTestBedSpecForm.get('numDuts').disable();
      } else {
        this.customTestBedSpecForm.get('numDuts').enable();

      }
    });

    this.customTestBedSpecForm.get('customHostSelection').valueChanges.subscribe(selection => {
      if (selection == CustomAssetSelection.SPECIFIC.toString()) {
        this.customTestBedSpecForm.get('numDuts').disable();
      } else {
        this.customTestBedSpecForm.get('numDuts').enable();

      }
    })

  }

  _getAssetSelectionKey(flatName) {
    return `${flatName}Selection`;
  }

  _getNumAssetsKey(flatName) {
    return `${flatName}NumAssets`;
  }

  _getSpecificAssetsKey(flatName) {
    return `${flatName}SpecificAssets`;
  }

  prepareFormGroup() {
    let group = {};
    group["selectedTestBed"] = new FormControl();

    this.assetTypes.forEach(assetType => {
      let flatName = this._flattenName(assetType);
      let assetSelectionKey = this._getAssetSelectionKey(flatName);
      let numAssetsKey = this._getNumAssetsKey(flatName);
      let specificAssetsKey = this._getSpecificAssetsKey(flatName);
      group(assetSelectionKey) = new
    })
  }

  _flattenName(name: string): string {  /* flatten DUT to dut, Perf Listener to "perf_listener"*/
    return name.toLowerCase().replace(" ", "_");
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
    console.log(this.customTestBedSpecForm.get("selectedDuts").value);

  }
}
