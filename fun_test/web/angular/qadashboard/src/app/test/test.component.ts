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
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";

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




  constructor(private apiService: ApiService, private logger: LoggerService, private userService: UserService, private router: Router, private route: ActivatedRoute,
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
  logDir: any;
  @Input() tags: string;
  suiteExecutionsCount: number;
  status: string = "Fetching Data";




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

    this.logDir = null;
    this.suiteExecutionsCount = 0;
    let payload = {};
    if (this.tags) {
      payload["tags"] = this.tags;
    }
    let self = this;
    new Observable(observer => {
      observer.next(true);
      //observer.complete();

      return () => {

      }
    }).pipe(switchMap(() => {
        return this.getQueryParam().pipe(switchMap((response) => {
          this.queryParameters = response;
          //this.setFilterButtons();
          return of(response);
        }))
      }),switchMap((response) => {
        if (response.hasOwnProperty('submitter_email')) {
          payload["submitter_email"] = response.submitter_email;
        }
        if (response.hasOwnProperty('test_bed_type')) {
          payload["test_bed_type"] = response.test_bed_type;
        }
        if (response.hasOwnProperty('suite_path')) {
          payload["suite_path"] = response.suite_path;
        }
        if (response.hasOwnProperty('tag')) {
          payload["tags"] = [response.tag];
        }

        let url = "/regression/suite_executions_count";
        if (!this.queryParameters.hasOwnProperty("state_filter")) {
          url += "/ALL";
          this.stateFilterString = this.stateStringMap.ALL;
        } else {
          url += "/" + this.queryParameters.state_filter;
          this.stateFilterString = this.stateStringMap[this.queryParameters.state_filter];
        }
        return this.apiService.post(url, payload).pipe(switchMap((result) => {
          this.suiteExecutionsCount = (parseInt(result.data));
          this.setPage(1);
          return of(true);
        }))
      })
    ).subscribe(() => {

    }, error => {
      this.logger.error(error);
    });

    if (!this.logDir) {
      this.apiService.get("/regression/log_path").subscribe(function (result) {
        self.logDir = result.data;
      }, error => {
        self.logDir = "/static/logs/s_";
      });
    }

    this.userService.getUserMap().subscribe((response) => {
      this.userMap = response;
    }, error => {
      this.logger.error("Unable to fetch usermap");
    });
    this.status = null;
  }


  getQueryParam() {
    return this.route.queryParams.pipe(switchMap(params => {
      if (params.hasOwnProperty('tag')) {
        this.tags = '["' + params["tag"] + '"]';
      }
      return of(params);
    }))
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

    }
    if (userSuppliedParams) {
      for (let key in userSuppliedParams) {
        queryParams[key] = userSuppliedParams[key];
      }
    }
    return queryParams;
  }

  onSubmit() {
    console.log('submitted');
  }

}


