import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup, Validators} from "@angular/forms";
import {TestBedService} from "../test-bed/test-bed.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";

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

  dropDownSettings = {};
  assetTypes: any = null;
  flattenedAssetTypeNames: string[] = [];
  flattenedAssetTypeNameMap: any = {};

  customTestBedSpecFormErrorMessage = null;

  newSuiteEntryForm = new FormGroup({
    path: new FormControl(''),
    testCaseIds: new FormControl(''),
    inputs: new FormControl('')
  });

  customTestBedSpecForm = null; /*new FormGroup({
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


  });*/

  constructor(private testBedService: TestBedService, private modalService: NgbModal) {

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
      this.customTestBedSpecForm = this.prepareFormGroup();
      let i = 0;
      this.customTestBedSpecForm.get('selectedTestBed').valueChanges.subscribe(selection => {
        this.selectedTestBed = selection;

        Object.keys(this.assetTypes).forEach(assetTypeKey => {
          let flatName = this._flattenName(assetTypeKey);
          let assetSelectionKey = this._getAssetSelectionKey(flatName);
          let numAssetsKey = this._getNumAssetsKey(flatName);
          let specificAssetsKey = this._getSpecificAssetsKey(flatName);
          this.customTestBedSpecForm.controls[specificAssetsKey].setValue(null);
          this.customTestBedSpecForm.controls[numAssetsKey].setValue(null);
          this.customTestBedSpecForm.controls[assetSelectionKey].setValue(CustomAssetSelection.NUM.toString());

        })

      })
    });



    /*
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
    })*/

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

    Object.keys(this.assetTypes).forEach(assetTypeKey => {
      let flatName = this._flattenName(assetTypeKey);
      this.flattenedAssetTypeNames.push(flatName);
      this.flattenedAssetTypeNameMap[flatName] = {name: this.assetTypes[assetTypeKey], data: null};
      let assetSelectionKey = this._getAssetSelectionKey(flatName);
      let numAssetsKey = this._getNumAssetsKey(flatName);
      let specificAssetsKey = this._getSpecificAssetsKey(flatName);
      group[assetSelectionKey] = new FormControl(CustomAssetSelection.NUM);
      group[numAssetsKey] = new FormControl();
      group[specificAssetsKey] = new FormControl();
      this.flattenedAssetTypeNameMap[flatName].data = [];
      this.assets.forEach(asset => {
        if (asset.type === this.assetTypes[assetTypeKey]) {
          this.flattenedAssetTypeNameMap[flatName].data.push(asset);
        }
      })

    });
    let fg = new FormGroup(group);
    fg.setValidators(this.customTestBedSpecValidator.bind(this));
    return fg;
  }

  customTestBedSpecValidator(group: FormGroup): { [key: string]: boolean } | null {
    this.customTestBedSpecFormErrorMessage = null;
    let valid = true;
    if (group.pristine) {

    } else {
      if (!group.get("selectedTestBed").value) {
        valid = false;
        this.customTestBedSpecFormErrorMessage = "Please select a test-bed";

      } else {
        let totalAssets = 0;

        for (let key of Object.keys(this.assetTypes)) {
          let flatName = this._flattenName(key);
          let readOut = this._readOutCustomTestBedSpecForm(flatName);
          totalAssets += readOut["numAssets"];
          let specificAssets = readOut["specificAssets"];
          if (specificAssets) {
            totalAssets += specificAssets.length;
          }
        }

        if (!totalAssets) {
          valid = false;
          this.customTestBedSpecFormErrorMessage = "At least one asset must be selected";
        }
      }


    }






    return {'valid': valid};
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

  filterAssetsBySelectedTestBed(allAssets) {  // Only choose assets that belong to the selected test-bed
    return allAssets.filter(asset => asset.test_beds.indexOf(this.selectedTestBed) > -1).map(o => { return o.name });
  }

  test() {
    console.log(this.customTestBedSpecForm.get(this._getAssetSelectionKey("dut")).value);
    //console.log(this.selectedTestBed.value);
     //console.log(this.selectedTestBed);
     //console.log(this.customTestBedSpecForm.get("selectedTestBed").value);
    // console.log(this.customTestBedSpecForm.get("customDutSelection").value);
    // console.log(this.customTestBedSpecForm.get("numDuts").value);
    // console.log(this.customTestBedSpecForm.get("selectedDuts").value);
    //console.log(this.flattenedAssetTypeNames);
    //console.log(this.flattenedAssetTypeNameMap);

  }

  _readOutCustomTestBedSpecForm(flatName) {
    let result = {};
    let assetSelectionKey = this._getAssetSelectionKey(flatName);
    let numAssetsKey = this._getNumAssetsKey(flatName);
    let specificAssetsKey = this._getSpecificAssetsKey(flatName);

    let assetSelection = this.customTestBedSpecForm.get(assetSelectionKey).value;
    result["assetSelection"] = assetSelection;

    let numAssets = parseInt(this.customTestBedSpecForm.get(numAssetsKey).value);
    if (isNaN(numAssets)) {
      numAssets = 0;
    }
    result["numAssets"] = numAssets;
    let specificAssets = this.customTestBedSpecForm.get(specificAssetsKey).value;
    result["specificAssets"] = specificAssets;

    return result;
  }

  onClickCustomTestBedSpec(content) {
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((dontCare) => {
      console.log("Ready to submit");
      let customTestBedSpec = {};
      let selectedTestBed = this.customTestBedSpecForm.get("selectedTestBed").value;



    }, ((reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    }));
  }
}
