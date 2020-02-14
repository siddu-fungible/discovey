import {Component, Input, OnInit} from '@angular/core';
import {AbstractControl, FormControl, FormGroup, Validators} from "@angular/forms";
import {TestBedService} from "../test-bed/test-bed.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {SuiteEditorService, Suite, SuiteEntry, SuiteMode} from "./suite-editor.service";
import {RegressionService} from "../regression.service";
import {LoggerService} from "../../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {UserProfile} from "../../login/definitions";
import {CommonService} from "../../services/common/common.service";
import {ApiService} from "../../services/api/api.service";

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
  mode: SuiteMode = SuiteMode.SUITE;
  SuiteMode = SuiteMode;
  userProfile: UserProfile = null;
  cloneId: number = null;

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
  customTestBedSpecPopulationStatus = null;

  availableCategories: string [] = null;
  availableSubCategories: string [] = ["general"];
  //selectedCategories: string [] = null;
  selectedSubCategories: string [] = null;

  availableTags: string[] = null;

  tags: string = null;
  suite: Suite = null;
  driver = null;
  users: any = null;
  selectedUser: any = null;

  editorPristine: boolean = true;

  poolMemberOptions = {}; //{"DUT": ["Default", "With servers", "With SSDs"]};
  userWantsToSubmit: boolean = false;

  constructor(private testBedService: TestBedService,
              private modalService: NgbModal,
              private service: SuiteEditorService,
              private regressionService: RegressionService,
              private loggerService: LoggerService,
              private route: ActivatedRoute,
              private commonService: CommonService,
              private apiService: ApiService) {

  }


  ngOnInit() {
    this.userProfile = this.commonService.getUserProfile();
    if (!this.userProfile) {
      this.loggerService.error("Unable to fetch user profile");
      return;
    }
    this.driver = new Observable(observer => {
      observer.next(true);
      return () => {
      }
    }).pipe(switchMap(response => {
      return this.fetchUsers();
    })).pipe(switchMap(response => {
      return this.getRouterQueryParam();
    })).pipe(switchMap(response => {
      return this.getRouterParam();
    })).pipe(switchMap(response => {
      return this.fetchSuite();
    })).pipe(switchMap(response => {
      return this.service.categories();
    })).pipe(switchMap(response => {
      this.availableCategories = response;
      return this.regressionService.tags();
    })).pipe(switchMap((response) => {
      this.availableTags = response;
      return this.testBedService.testBeds();
    })).pipe(switchMap(response => {
      this.testBeds = response;
      this.testBeds = this.testBeds.filter(testBed => testBed.name.startsWith('fs'));
      return this.testBedService.assetTypes();
    })).pipe(switchMap(response => {
      this.assetTypes = response;

      return this.testBedService.assets();
    })).pipe(switchMap(response => {
      this.assets = response;
      return of(true);
    }));

    setTimeout(() => {
      this.customTestBedSpecPopulationStatus = "Refreshing";
      this.refreshAll();
    }, 1);

  }

  getRouterParam() {
    return this.route.params.pipe(switchMap(params => {
      if (params["id"]) {
        this.id = params["id"];
      }
      return of(this.id)
    }));
  }

  fetchSuite() {
    let userEmail = this.userProfile.user.email;
    if (!this.id && !this.cloneId) {
      this.suite = new Suite();
      this.suite.type = this.mode;
      this.setSelectedUser(userEmail);
      return of(this.suite)

    } else {
      let id = this.cloneId;
      if (this.id) {
        id = this.id;
      }
      return this.service.suite(id).pipe(switchMap(response => {
        this.suite = response;
        userEmail = this.suite.suite_owner;
        this.setSelectedUser(userEmail);
        console.log(this.suite.constructor.name);
        return of(this.suite)
      }));
    }
  }

  setSelectedUser(userEmail) {
    for (let user of this.users) {
      if (user.email === userEmail) {
        this.selectedUser = user;
        break;
      }
    }
  }

  getRouterQueryParam() {
    return this.route.queryParams.pipe(switchMap(params => {
      if (params.hasOwnProperty('mode')) {
        this.mode = params["mode"];
      }
      if (params.hasOwnProperty('clone_id')) {
        this.cloneId = params['clone_id'];
      }
      return of(params);
    }))
  }

  refreshAll() {
    //this.customTestBedSpecPopulationStatus = "Refreshing";

    this.driver.subscribe(response => {
      this.customTestBedSpecForm = this.prepareFormGroup();
      if (this.suite) {
        this.prepareCustomTestBedSpecValidated();
        this.customTestBedSpecPopulationStatus = null;
      }
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

    }, error => {
      this.customTestBedSpecPopulationStatus = null;
    });
  }

  prepareCustomTestBedSpecValidated() {
    let baseTestBed = null;
    let selectedTestBedValue = this.customTestBedSpecForm.get("selectedTestBed").value;

    if (selectedTestBedValue) {
      baseTestBed = selectedTestBedValue.name;
    }
    if (baseTestBed) {
      console.log("Started");
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

        } else if (this.poolMemberOptions.hasOwnProperty(flatName)) {
          let payloadDict = {};
          let options = this.poolMemberOptions[flatName];
          for (let i = 0; i < options.length; i++) {
            let poolMemberSelectionKey = this._getPoolMemberSelectionKey(flatName, options[i]);
            let poolMemberSelectionValue = readOut[poolMemberSelectionKey];
            if (!isNaN(poolMemberSelectionValue)) {
              payloadDict[i] = {"num": poolMemberSelectionValue};
              totalAssets += readOut[poolMemberSelectionKey];
            }

          }

          ref["pool_member_type_options"] = payloadDict;
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
      this.suite.custom_test_bed_spec = this.customTestBedValidated;
    }
  }

  _getPoolMemberOptionsString(assetType, options) {
    let s = ``;
    Object.keys(options).forEach(option => {
      s += `${this.poolMemberOptions[this._flattenName(assetType)][option]}: ${options[option].num}, `;
    });
    s = s.replace(/, $/, "");
    return s;
  }

  _getAssetSelectionKey(flatName) {
    return `${flatName}Selection`;
  }

  _getPoolMemberSelectionKey(flatName, poolMemberType) {
    return `${flatName}${poolMemberType}PoolMemberSelection`;
  }

  _getNumAssetsKey(flatName) {
    return `${flatName}NumAssets`;
  }

  _getSpecificAssetsKey(flatName) {
    return `${flatName}SpecificAssets`;
  }

  _getPoolMemberTypeString(assetType, poolMemberType) {
    let flatName = this._flattenName(assetType);
    return this.poolMemberOptions[flatName][parseInt(poolMemberType)];
  }

  _getTestBedByName(name) {
    let result = null;
    for (let i = 0; i < this.testBeds.length; i++) {
      if (this.testBeds[i].name === name) {
        result = this.testBeds[i];
        break;
      }
    }
    return result;
  }

  prepareFormGroup() {
    let group = {};

    group["selectedTestBed"] = new FormControl();
    if (this.suite && this.suite.custom_test_bed_spec) {
      if (Object.keys(this.suite.custom_test_bed_spec).indexOf('base_test_bed')) {
        let baseTestBed = this.suite.custom_test_bed_spec.base_test_bed;
        group["selectedTestBed"].setValue(this._getTestBedByName(baseTestBed));
      }
    }

    Object.keys(this.assetTypes).forEach(assetTypeKey => {
      let flatName = this._flattenName(assetTypeKey);
      if (assetTypeKey === "DUT") {
        this.poolMemberOptions[flatName] = ["Default", "With servers", "With SSDs"];
      }

      this.flattenedAssetTypeNames.push(flatName);
      let assetTypeValue = this.assetTypes[assetTypeKey];
      this.flattenedAssetTypeNameMap[flatName] = {name: this.assetTypes[assetTypeKey], data: null};
      let assetSelectionKey = this._getAssetSelectionKey(flatName);
      let numAssetsKey = this._getNumAssetsKey(flatName);
      let specificAssetsKey = this._getSpecificAssetsKey(flatName);


      if (this.poolMemberOptions.hasOwnProperty(flatName)) {
        let options = this.poolMemberOptions[flatName];
        options.forEach(option => {
          let poolMemberSelectionKey = this._getPoolMemberSelectionKey(flatName, option);
          group[poolMemberSelectionKey] = new FormControl(0);
        });
      }

      group[assetSelectionKey] = new FormControl(CustomAssetSelection.NUM);
      group[numAssetsKey] = new FormControl();
      group[specificAssetsKey] = new FormControl();
      if (this.suite.custom_test_bed_spec && this.suite.custom_test_bed_spec.hasOwnProperty('asset_request')) {
        let assetRequest = this.suite.custom_test_bed_spec.asset_request;
        if (assetRequest.hasOwnProperty(assetTypeValue)) {
          let num = null;
          let names = null;
          let poolMemberType = null;
          if (assetRequest[assetTypeValue].hasOwnProperty("num")) {
            num = assetRequest[assetTypeValue]["num"];
            /*if (assetRequest[assetTypeValue].hasOwnProperty('pool_member_type')) {
              poolMemberType = assetRequest[assetTypeValue]["pool_member_type"];
            }*/
          }
          if (assetRequest[assetTypeValue].hasOwnProperty("names")) {
            names = assetRequest[assetTypeValue]["names"]
          }
          if (num !== null) {
            group[assetSelectionKey].setValue(CustomAssetSelection.NUM);
            group[numAssetsKey].setValue(num);


          } else if (assetRequest[assetTypeValue].hasOwnProperty('pool_member_type_options')) {
            group[assetSelectionKey].setValue(CustomAssetSelection.NUM);
            let poolMemberTypeOptions = assetRequest[assetTypeValue]['pool_member_type_options'];
            Object.keys(poolMemberTypeOptions).forEach(poolMemberType => {
              let value = poolMemberTypeOptions[poolMemberType]["num"];
              let poolMemberTypeKey = this._getPoolMemberSelectionKey(flatName, this.poolMemberOptions[flatName][parseInt(poolMemberType)]);
              group[poolMemberTypeKey].setValue(value);
            });

          }
          if (names) {
            group[assetSelectionKey].setValue(CustomAssetSelection.SPECIFIC);
            group[specificAssetsKey].setValue(names);
          }
        }
      }


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
          let numAssets = readOut["numAssets"];
          if (isNaN(numAssets)) {
            numAssets = 0;
          }
          totalAssets += numAssets;
          let specificAssets = readOut["specificAssets"];
          if (specificAssets) {
            totalAssets += specificAssets.length;
          }

          if (this.poolMemberOptions.hasOwnProperty(flatName)) {
            let options = this.poolMemberOptions[flatName];
            for (let i = 0; i < options.length; i++) {
              let poolMemberSelectionKey = this._getPoolMemberSelectionKey(flatName, options[i]);
              let poolMemberSelectionValue = readOut[poolMemberSelectionKey];
              if (!isNaN(poolMemberSelectionValue)) {
                totalAssets += poolMemberSelectionValue;
              }
            }
          }


        }

        if (!totalAssets) {
          valid = false;
          errorMessage = "At least one asset must be selected";
        }
      }


    }

    return valid ? null : {'errorMessage': errorMessage};
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


  filterAssetsBySelectedTestBed(selectedTestBed, allAssets) {  // Only choose assets that belong to the selected test-bed
    return allAssets.filter(asset => asset.test_beds.indexOf(selectedTestBed) > -1).map(o => {
      return o.name
    });
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

    if (parseInt(assetSelection) === CustomAssetSelection.NUM) {
      let numAssets = parseInt(this.customTestBedSpecForm.get(numAssetsKey).value);
      if (isNaN(numAssets)) {
        numAssets = 0;
      }
      result["numAssets"] = numAssets;

      if (this.poolMemberOptions.hasOwnProperty(flatName)) {
        let options = this.poolMemberOptions[flatName];
        options.forEach(option => {
          let poolMemberSelectionKey = this._getPoolMemberSelectionKey(flatName, option);
          result[poolMemberSelectionKey] = this.customTestBedSpecForm.get(poolMemberSelectionKey).value;
        });
      }

    } else {
      let specificAssets = this.customTestBedSpecForm.get(specificAssetsKey).value;
      result["specificAssets"] = specificAssets;
    }
    return result;
  }

  _hasKey(o, key) {
    console.log(o);
    return Object.keys(o).indexOf(key) > -1;
  }

  onAddCustomTestBedSpec(content) {
    this.modalService.open(content, {
      ariaLabelledBy: 'modal-basic-title',
      size: 'lg',
      backdrop: 'static'
    }).result.then((dontCare) => {
      console.log("Ready to submit");
      let customTestBedSpec = {};
      this.prepareCustomTestBedSpecValidated();

    }, ((reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    }));
  }

  onEditCustomTestBedSpec(content) {
    this.modalService.open(content, {
      ariaLabelledBy: 'modal-basic-title',
      size: 'lg',
      backdrop: 'static'
    }).result.then((dontCare) => {
      console.log("Ready to submit");
      let customTestBedSpec = {};
      this.prepareCustomTestBedSpecValidated();

    }, ((reason) => {
      console.log("Rejected");
      //this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    }));
  }

  onDeleteCustomTestBedSpec() {
    this.customTestBedSpecForm.reset();
    this.customTestBedValidated = null;
    this.suite.custom_test_bed_spec = null;
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
    this.editorPristine = false;
  }

  onShortDescriptionChangedEvent(shortDescription) {
    this.suite.short_description = shortDescription;
    this.editorPristine = false;
  }

  fetchUsers(): any {
    return this.apiService.get("/api/v1/users").pipe(switchMap(response => {
      this.users = response.data;
      return of(true);
    }));
  }

  onSubmitSuite() {
    if (!this.id || this.cloneId) {
      this.service.add(this.suite).subscribe(response => {
        this.loggerService.success("Added suite");
        this.editorPristine = true;
        setTimeout(() => {
          window.location.href = "/regression/suites_view";
        }, 1000);

      })
    } else {
      this.service.replace(this.suite, this.id).subscribe(response => {
        this.loggerService.success("Updated suite");
        setTimeout(() => {
          window.location.href = "/regression/suites_view";
        }, 1000);

      })
    }

  }

  onSelect() {
    //console.log("Filter change");
    this.editorPristine = false;
  }


  onDeleteSuiteEntry(index) {
    this.suite.entries.splice(index, 1);
  }

  _hasPoolMemerOptions(flatName) {
    return Object.keys(this.poolMemberOptions).indexOf(flatName) > -1;
  }

  _getPoolMemberOptions(flatName) {
    console.log(this.poolMemberOptions[flatName]);
  }

  submitEnter(enter) {
    this.userWantsToSubmit = enter;
  }
}
