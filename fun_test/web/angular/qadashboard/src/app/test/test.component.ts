import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";
import {RegressionService} from "../regression/regression.service";
import {FormControl, FormGroup} from "@angular/forms";
import {FormBuilder, Validators} from "@angular/forms";
import {NgMultiSelectDropDownModule} from 'ng-multiselect-dropdown';
import {UserService} from "../services/user/user.service";
import {ActivatedRoute, Router} from "@angular/router";

class FilterButton {
  displayString: string = null;
  filterKey: string = null;
  filterValue: string = null;
  stateStringMap = null;
  constructor(filterKey, filterValue, stateStringMap) {
    this.filterKey = filterKey;
    this.filterValue = filterValue;
    this.stateStringMap = stateStringMap;
    this._setDisplayString();
  }

  _setDisplayString() {
    let keyString = this.filterKey;
    let keyValue = this.filterValue;
    if (keyString === 'state_filter') {
      keyString = "State";
      if (keyValue !== 'ALL') {
        keyValue = this.stateStringMap[keyValue];
      }
    }
    if (keyString === 'submitter_email') {
      keyString = "Submitter";
    }
    if (keyString === 'test_bed_type') {
      keyString = "Test-bed";
    }
    if (keyString === 'suite_path') {
      keyString = "Suite";
    }
    this.displayString = `${keyString}=${keyValue}`;
  }

  setData(filterKey, filterValue): void  {
    this.filterKey = filterKey;
    this.filterValue = filterValue;
  }
}

enum Filter {
  ALL = "ALL",
  COMPLETED = "COMPLETED",
  IN_PROGRESS = "IN_PROGRESS",
  QUEUED = "QUEUED",
  SCHEDULED = "SCHEDULED",
  SUBMITTED = "SUBMITTED",
  AUTO_SCHEDULED = "AUTO_SCHEDULED"
}



@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})

export class TestComponent implements OnInit {




  constructor(private apiService: ApiService, private logger: LoggerService, private userService: UserService, private router: Router,
              private renderer: Renderer2, private commonService: CommonService, private regressionService: RegressionService,
              private fb: FormBuilder) {
  }

  searchForm : FormGroup;
  dropdownList = [];
  selectedItems = [];
  dropdownSettings = {};
  userMap: any = null;
  submitter_emails : any = [];
  fetched : boolean = false;
  stateFilterString: string = "ALL";
  filter = Filter;
  stateStringMap: any = null;
  stateMap: any = null;
  queryParameters: any = null;
  filterButtons: FilterButton [] = [];



  ngOnInit() {
    this.searchForm = this.fb.group({
    submitters: [[]],
    executionId: [''],
    suiteName: ['']
  });

    this.userService.getUserMap().subscribe((response) => {
      this.userMap = response;
      for (let user of Object.keys(this.userMap)){
        this.submitter_emails.push(user);
      }
      this.fetched = true;
    }, error => {
      this.logger.error("Unable to fetch usermap");
    });

    this.dropdownSettings = {
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      itemsShowLimit: 3,
      allowSearchFilter: true
    };
  }

  onItemSelect(item: any) {
    console.log(item);
  }

  onSelectAll(items: any) {
    console.log(items);
  }

  get submitters() {
    return this.searchForm.get('submitters');
  }

  loadAPIData() {
    this.searchForm.patchValue({
      userName: 'Bruce',
      password: 'test',
      confirmPassword: 'test'
    });
  }

    navigateByQueryParams(userParams) {
    let queryParams = this.prepareBaseQueryParams(userParams);
    this.router.navigate(['/regression'], {queryParams: queryParams});
  }

  navigateByQuery(state) {
    let queryPath = "/regression?state_filter=" + state;
    let userParams = {state_filter: state};
    this.router.navigate(['/regression'], {queryParams: this.prepareBaseQueryParams(userParams)});
  }

    prepareBaseQueryParams(userSuppliedParams) {
    let queryParams = {};
    if (this.queryParameters) {
      if (this.queryParameters.hasOwnProperty('submitter_email')) {
        queryParams["submitter_email"] = this.queryParameters['submitter_email'];
      }

      if (this.queryParameters.hasOwnProperty('test_bed_type')) {
        queryParams["test_bed_type"] = this.queryParameters["test_bed_type"];
      }

      if (this.queryParameters.hasOwnProperty('suite_path')) {
        queryParams["suite_path"] = this.queryParameters["suite_path"]
      }

      if (this.queryParameters.hasOwnProperty('tag')) {
        queryParams["tag"] = this.queryParameters["tag"]
      }

      /*if (this.queryParameters.hasOwnProperty('state_filter')) {
        queryParams["state_filter"] = this.queryParameters["state_filter"];
        //this.stateFilterString = this.stateStringMap[this.queryParameters['state_filter']];
      } else {
        this.stateFilterString = "ALL";
      }*/
    }
    if (userSuppliedParams) {
      for (let key in userSuppliedParams) {
        queryParams[key] = userSuppliedParams[key];
      }
    }
    //console.log(queryParams);
    return queryParams;
  }

}


