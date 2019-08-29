import {Component, Input, OnInit} from '@angular/core';
import {AbstractControl, FormControl, FormGroup, Validators} from "@angular/forms";
import {TestBedService} from "../test-bed/test-bed.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {SuiteEditorService, Suite, SuiteEntry} from "./suite-editor.service";
import {RegressionService} from "../regression.service";
import {LoggerService} from "../../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";


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
  @Input() id: number = null;
  testCaseIds: number[] = null;
  inputs: any = null;
  customTestBedSpec: any = null;
  addingCustomTestBedSpec: boolean = true;
  inputsExample: string = '{"abc":123}';
  testBeds: any = null;
  assets: any = null;
  addingScript: boolean = null;

  dutAssets: any = [];
  hostAssets: any = [];
  perfListenerAssets: any = [];


  CustomAssetSelection = CustomAssetSelection;

  dropDownSettings = {};
  assetTypes: any = null;
  flattenedAssetTypeNames: string[] = [];
  flattenedAssetTypeNameMap: any = {};

  customTestBedSpecFormErrorMessage = null;
  currentScriptPath: string = null;

  name: string = "Some suite name";
  shortDescription: string = "Short description";

  customTestBedSpecForm = null;
  customTestBedValidated = null;

  availableCategories: string [] = ["networking", "storage", "accelerators", "security", "system"];
  availableSubCategories: string [] = ["general"];
  //selectedCategories: string [] = null;
  selectedSubCategories: string [] = null;

  availableTags: string[] = null;

  tags: string = null;
  suite: Suite = null;
  driver = null;

  constructor(private testBedService: TestBedService,
              private modalService: NgbModal,
              private service: SuiteEditorService,
              private regressionService: RegressionService,
              private loggerService: LoggerService,
              private route: ActivatedRoute) {

  }


  ngOnInit() {


    this.driver = new Observable(observer => {
      observer.next(true);
      return () => {
      }
    }).pipe(switchMap(response => {
      return this.regressionService.tags();
    })).pipe(switchMap((response) => {
      this.availableTags = response;
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
    }));


    this.route.params.subscribe(params => {
      if (params["id"]) {
        this.id = params["id"];
      }
      if (!this.id) {
        this.suite = new Suite();

      } else {
        this.service.suites(this.id).subscribe(response => {
          this.suite = response;
          this.refreshAll();
        })
      }

    });




  }

  refreshAll() {
    this.driver.subscribe(response => {
      this.customTestBedSpecForm = this.prepareFormGroup();
      let i = 0;
      this.customTestBedSpecForm.get('selectedTestBed').valueChanges.subscribe(selection => {
        //this.selectedTestBed = selection;

        Object.keys(this.assetTypes).forEach(assetTypeKey => {
          let flatName = this._flattenName(assetTypeKey);
          let assetSelectionKey = this._getAssetSelectionKey(flatName);
          let numAssetsKey = this._getNumAssetsKey(flatName);
          let specificAssetsKey = this._getSpecificAssetsKey(flatName);
          this.customTestBedSpecForm.controls[specificAssetsKey].setValue(null);
          this.customTestBedSpecForm.controls[numAssetsKey].setValue(null);
          this.customTestBedSpecForm.controls[assetSelectionKey].setValue(CustomAssetSelection.NUM.toString());

        })

      });

      this.customTestBedSpecForm.statusChanges.subscribe(status => {
        if (status === "VALID") {
        } else {
          this.customTestBedValidated = null;
        }

      })

    });
  }

  prepareCustomTestBedSpecValidated() {
    this.customTestBedValidated = {};
    this.customTestBedValidated["base_test_bed"] = this.customTestBedSpecForm.get("selectedTestBed").value.name;
    let payload = {};
    let assetRequests = [];
    for (let key of Object.keys(this.assetTypes)) {
      let flatName = this._flattenName(key);
      let readOut = this._readOutCustomTestBedSpecForm(flatName);
      //console.log(readOut);

      let ref = {};
      //let ref = payload[this.flattenedAssetTypeNameMap[flatName].name];
      let totalAssets = 0;
      if (readOut["numAssets"] > 0) {
        ref["num"] = readOut["numAssets"];
        totalAssets += readOut["numAssets"];
      }

      let specificAssets = readOut["specificAssets"];
      if (specificAssets && specificAssets.length > 0) {
        ref["names"] = readOut["specificAssets"];
        totalAssets += readOut["specificAssets"].length;
      }
      if (totalAssets) {
        let key = this.flattenedAssetTypeNameMap[flatName].name;
        let tempDict = {};
        tempDict[key] = ref;
        assetRequests.push(tempDict);
      }
    }
    if (assetRequests.length) {
      payload["asset_request"] = {};
      assetRequests.forEach(assetRequest => {
        let thisKey = Object.keys(assetRequest)[0];
        payload["asset_request"][thisKey] = assetRequest[thisKey];
      })
    }
    this.customTestBedValidated["asset_request"] = payload["asset_request"];
    console.log(payload);

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
    let errorMessage = null;
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
          errorMessage = "At least one asset must be selected";
        }
      }


    }

    return valid? null: {'errorMessage': errorMessage};
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

  filterAssetsBySelectedTestBed(selectedTestBed, allAssets) {  // Only choose assets that belong to the selected test-bed
    return allAssets.filter(asset => asset.test_beds.indexOf(selectedTestBed) > -1).map(o => { return o.name });
  }

  test() {
    //console.log(this.customTestBedSpecForm.get(this._getAssetSelectionKey("dut")).value);
    //console.log(this.selectedTestBed.value);
     //console.log(this.selectedTestBed);
    //console.log(this.customTestBedSpecForm.get("selectedTestBed").value);
    // console.log(this.customTestBedSpecForm.get("customDutSelection").value);
    // console.log(this.customTestBedSpecForm.get("numDuts").value);
    // console.log(this.customTestBedSpecForm.get("selectedDuts").value);
    //console.log(this.flattenedAssetTypeNames);
    //console.log(this.flattenedAssetTypeNameMap);
    //console.log(this.selectedCategories);
    console.log(this.suite);

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

  _hasKey(o, key) {
    return Object.keys(o).indexOf(key) > -1;
  }

  onAddCustomTestBedSpec(content) {
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((dontCare) => {
      console.log("Ready to submit");
      let customTestBedSpec = {};
      this.prepareCustomTestBedSpecValidated();

    }, ((reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    }));
  }

  onEditCustomTestBedSpec(content) {
    this.modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((dontCare) => {
      console.log("Ready to submit");
      let customTestBedSpec = {};
      this.prepareCustomTestBedSpecValidated();

    }, ((reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    }));
  }

  singleSelectScriptPathEvent(scriptPath) {
    if (scriptPath) {
      this.currentScriptPath = scriptPath;
    }
    //console.log(scriptPath);
  }

  onAddScript() {
    this.addingScript = true;
  }

  _clearNewSuiteEntry() {
    this.currentScriptPath = null;
    this.inputs = null;
    this.testCaseIds = null;
  }

  onSubmitNewSuiteEntry() {
    console.log("Submitting new suite entry");
    this.addingScript = false;
    let suiteEntry = new SuiteEntry();
    suiteEntry.script_path = this.currentScriptPath;
    suiteEntry.inputs = this.inputs;
    suiteEntry.test_case_ids = this.testCaseIds;
    console.log(suiteEntry);
    this.suite.addEntry(suiteEntry);
    this._clearNewSuiteEntry();
  }

  onCancelNewSuiteEntry() {
    this.addingScript = false;
  }

  onNameChangedEvent(name) {
    this.suite.name = name;
  }

  onShortDescriptionChangedEvent(shortDescription) {
    this.suite.short_description = shortDescription;
  }

  onSubmitSuite() {
    if (!this.id) {
      this.service.add(this.suite).subscribe(response => {
        this.loggerService.success("Added suite");
      })
    } else {
      this.service.replace(this.suite, this.id).subscribe(response => {
        this.loggerService.success("Updated suite");
      })
    }

  }

}
