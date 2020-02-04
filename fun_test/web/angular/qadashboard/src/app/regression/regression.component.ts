import {
  Component,
  OnInit,
  Input, ViewChild
} from '@angular/core';
import {PagerService} from "../services/pager/pager.service";
import {ApiService} from "../services/api/api.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Title} from "@angular/platform-browser";
import {ReRunService} from "./re-run.service";
import {LoggerService} from '../services/logger/logger.service';
import {RegressionService} from "./regression.service";
import {Observable, of, merge} from "rxjs";
import {switchMap} from "rxjs/operators";
import {UserService} from "../services/user/user.service";
import {NgbModal, ModalDismissReasons} from '@ng-bootstrap/ng-bootstrap';
import {FormGroup} from "@angular/forms";
import {FormBuilder, Validators, AbstractControl} from "@angular/forms";
import {
  trigger,
  state,
  style,
  animate,
  transition,
} from '@angular/animations';
import {SuiteEditorService, Suite} from "./suite-editor/suite-editor.service";

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

  setData(filterKey, filterValue): void {
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
  selector: 'app-regression',
  templateUrl: './regression.component.html',
  styleUrls: ['./regression.component.css'],
  animations: [trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(300)
      ]),
      transition(':leave', [
        animate(1, style({ opacity: 1.0 }))
      ]),
      state('*', style({ opacity: 1.0 })),
    ])]
})

export class RegressionComponent implements OnInit {
  @ViewChild('searchForm') formValues;
  searching: boolean = false;
  searchingByExecutionId: boolean = false;
  pager: any = {};
  suiteExecutionsCount: number;
  recordsPerPage: number;
  @Input() tags: string;
  items: any;
  logDir: any;
  status: string = "Fetching Data";
  //stateFilter: string = null; //Filter.ALL;
  stateFilterString: string = "ALL";
  filter = Filter;
  stateStringMap: any = null;
  stateMap: any = null;
  queryParameters: any = null;
  filterButtons: FilterButton [] = [];
  userMap: any = null;
  showingTestBeds: boolean = false;
  showingQueues: boolean = false;
  searchForm: FormGroup;
  selectedItems = [];
  dropDownSettings = {};
  submitterEmails: any = [];
  fetchedUsers: boolean = false;
  fetchedSuites: boolean = false;
  suitesInfo: any;
  suitesInfoKeys: any = [];
  suiteMap: {[key: number]: Suite} = {};

  // Re-run options
  reRunOptionsReRunFailed: boolean = false;
  reRunOptionsReRunAll: boolean = true;
  reUseBuildImage: boolean = false;


  constructor(private pagerService: PagerService,
              private apiService: ApiService,
              private route: ActivatedRoute,
              private title: Title,
              private reRunService: ReRunService,
              private logger: LoggerService,
              private regressionService: RegressionService,
              private router: Router,
              private userService: UserService,
              private fb: FormBuilder,
              private modalService: NgbModal,
              private suiteService: SuiteEditorService) {
    this.stateStringMap = this.regressionService.stateStringMap;
    this.stateMap = this.regressionService.stateMap;
  }

  ngOnInit() {
    this.searchForm = this.fb.group({
      submitters: [[]],
      executionId: [{value: '',disabled: true}],
      suiteName: [''],
      searchByExecutionId: ['']
    }, {validator: this.atLeastOneValidator});

    this.searchForm.get('searchByExecutionId').valueChanges
      .subscribe(v => {
        if (v){
          this.searchingByExecutionId = true;
          this.searchForm.get('executionId').enable();
        }
        else{
          this.searchingByExecutionId = false;
          this.searchForm.get('executionId').disable();
        }
      });

    this.dropDownSettings = {
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      itemsShowLimit: 3,
      allowSearchFilter: true,
    };
    this.title.setTitle('Regression');
    /*if (this.route.snapshot.data["tags"]) {
      this.tags = this.route.snapshot.data["tags"];
    }*/

    this.recordsPerPage = 50;
    this.logDir = null;
    this.suiteExecutionsCount = 0;
    /*if (this.tags) {
      payload["tags"] = this.tags;
    }*/
    let self = this;
    new Observable(observer => {
      observer.next(true);
      //observer.complete();

      return () => {

      }
    }).pipe(switchMap(() => {
        return this.getQueryParam().pipe(switchMap((response) => {
          this.queryParameters = response;
          this.setFilterButtons();
          return of(response);
        }))
      }), switchMap((response) => {
        let payload = {};

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

    this.suiteService.suites<Suite[]>(null, 1000, 1).subscribe(response => {
      let allSuites = response;
      allSuites.forEach(suite => {
        this.suiteMap[suite.id] = suite;
        this.suitesInfoKeys.push(suite.name);
      });
      this.suitesInfoKeys.sort();
      this.fetchedSuites = true;
    });

    /*
    this.suites().subscribe((response) => {
      this.suitesInfo = response;

      for (let suites of Object.keys(this.suitesInfo)) {
        this.suitesInfoKeys.push(suites);
      }
      this.suitesInfoKeys.sort();

      this.fetchedSuites = true;
    });*/

    this.userService.getUserMap().subscribe((response) => {
      this.userMap = response;
      for (let user of Object.keys(this.userMap)) {
        this.submitterEmails.push(user);
      }
      this.fetchedUsers = true;
    }, error => {
      this.logger.error("Unable to fetch usermap");
    });
    this.status = null;
  }

  setFilterButtons() {
    this.filterButtons = [];
    for (let key in this.queryParameters) {
      if (this.queryParameters[key]) {
        let fb = new FilterButton(key, this.queryParameters[key], this.stateStringMap);
        this.filterButtons.push(fb);
      }
    }
    //console.log(this.filterButtons);
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

  stateFilterStringToNumber(s) {
    let match = "ALL";
    for (let key in this.stateStringMap) {
      let value = this.stateStringMap[key];
      if (value === s) {
        match = key;
        break;
      }
    }
    return match;
  }

  onDeleteSuiteExecution(suiteExecution) {
    let executionId = suiteExecution.fields.execution_id;
    if (confirm(`Are you sure you want to delete ${executionId}`)) {
      let url = "/api/v1/regression/suite_executions/" + executionId;
      this.apiService.delete(url).subscribe(response => {
        this.logger.success(`Suite: ${executionId} deletion request submitted`);
        window.location.reload();
      }, error => {
        this.logger.error("Deletion failed");
      })
    }
  }

  onStateFilterClick(state) {
    let userParams = {state_filter: state};
    this.stateFilterString = this.stateStringMap[state];
    this.router.navigate(['/regression'], {queryParams: this.prepareBaseQueryParams(userParams)});
    /*
    this.stateFilterString = state;
    this.stateFilter = this.stateFilterStringToNumber(state);
    this.navigateByQuery(this.stateFilter);*/
  }

  navigateByQueryParams(userParams) {
    //userParams = [{'submitter_email': 'john.a@fungible.com'},{'submitter_email': 'ashwin.s@fungible.com'}];
    let queryParams = {};
    for (let userParam of userParams) {
      let key = Object.keys(userParam)[0];
      if ((key == 'submitter_email' || key == 'suite_path') && Array.isArray(userParam[key])) {
        queryParams[key] = this._flatten(userParam[key]);
      } else {
        queryParams[key] = userParam[key];
      }
    }
    this.router.navigate(['/regression'], {queryParams: this.prepareBaseQueryParams(queryParams)});
  }

  navigateByQuery(state) {
    let queryPath = "/regression?state_filter=" + state;
    let userParams = {state_filter: state};
    this.router.navigate(['/regression'], {queryParams: this.prepareBaseQueryParams(userParams)});
  }

  getQueryParam() {
    return this.route.queryParams.pipe(switchMap(params => {
      if (params.hasOwnProperty('tag')) {
        this.tags = '["' + params["tag"] + '"]';
      }
      return of(params);
    }))
  }

  setPage(page) {

    this.items = null;
    this.pager = this.pagerService.getPager(this.suiteExecutionsCount, page, this.recordsPerPage);
    if (page === 0 || (page > this.pager.endPage)) {

      return;
    }
    let payload = {};

    /*if (this.tags) {
      payload["tags"] = this.tags;
    }*/

    if (this.queryParameters) {
      for (let key in this.queryParameters) {
        payload[key] = this.queryParameters[key];
      }
    }

    this.status = "Fetching Data";
    let stateFilter = "ALL";
    if (this.queryParameters.hasOwnProperty("state_filter")) {
      stateFilter = this.queryParameters["state_filter"];
    }
    this.apiService.post("/regression/suite_executions/" + this.recordsPerPage + "/" + page + "/" + stateFilter, payload).subscribe(result => {
      this.items = result.data;
      this.items.map(item => this.applyAdditionalAttributes(item));
      this.items
        .map(item => this.getReRunInfo(item));
      this.status = null;
    });

  }

  applyAdditionalAttributes(item) {
    item["showingDetails"] = false;
    if (item.hasOwnProperty('fields') && item.fields.hasOwnProperty('environment')) {
      let environment = JSON.parse(item.fields.environment);
      if (environment && environment.hasOwnProperty('with_jenkins_build') && environment.with_jenkins_build) {
        if (environment.hasOwnProperty('build_parameters')) {
          if (environment.build_parameters.hasOwnProperty('BRANCH_FunOS')) {
            item["BRANCH_FunOS"] = environment.build_parameters.BRANCH_FunOS ? environment.build_parameters.BRANCH_FunOS : "master";
          }
        }
      }
      item["parsedEnvironment"] = environment;
    }
    if (item.hasOwnProperty('fields') && item.fields.hasOwnProperty('inputs')) {
      let inputs = JSON.parse(item.fields.inputs);
      item["parsedInputs"] = inputs;
    }
  }

  showDetailsClick(item) {
    item["showingDetails"] = !item["showingDetails"];
  }

  getReRunInfo(suiteExecution) {
    if (suiteExecution.fields.suite_type === 'regular') {
      this.reRunService.getOriginalSuiteReRunInfo(suiteExecution.fields.execution_id).subscribe(response => {
        suiteExecution["reRunInfo"] = response;
      }, error => {

      })
    } else if (suiteExecution.fields.suite_type === 'dynamic') {
      this.reRunService.getReRunSuiteInfo(suiteExecution.fields.execution_id).subscribe(response => {
        suiteExecution["reRunInfo"] = response;
      }, error => {

      })
    }

  }

  getReRunOriginalSuitePath(suiteExecution) {
    let suitePath = "*";
    if (suiteExecution) {
      if (suiteExecution.reRunInfo) {
        if (suiteExecution.reRunInfo.reRunInfo.length > 0) {
          suitePath = suiteExecution.reRunInfo.reRunInfo[0].original.attributes.suite_path;
        }
      }
    }
    return suitePath;
  }

  testCaseLength = function (testCases) {
    return JSON.parse(testCases).length;
  };

  trimTime(t) {
    return this.regressionService.getPrettyLocalizeTime(t);
  }

  /*
  getSuiteDetail(suiteId) {
    console.log(suiteId);
    window.location.href = "/regression/suite_detail/" + suiteId;
  }*/

  getSchedulerLog(suiteId) {
    return this.regressionService.getSchedulerLog(suiteId);
    /*
    if (this.logDir) {
      return this.logDir + suiteId + "/scheduler.log.txt"; // TODO
    }*/
  }

  getSchedulerLogDir(suiteId) {
    return this.regressionService.getSchedulerLogDir(suiteId);
    /*
    if (this.logDir) {
      return "/regression/static_serve_log_directory/" + suiteId;
    }*/
  }

  reRunClick(suiteExecution, resultFilter=null, reUseBuildImage=null) {
    this.reRunService.submitReRun(suiteExecution.fields.execution_id, suiteExecution.fields.suite_id, resultFilter, null, reUseBuildImage).subscribe(response => {
      this.logger.success("Re-run request submitted");
      window.location.href = "/regression";
    }, error => {
      this.logger.error("Error submitting re-run");
    });
  }

  killClick(suiteId) {
    this.regressionService.killSuite(suiteId).subscribe((result) => {
      this.logger.success(`Killed job: ${result}`);
      window.location.reload()
    }, error => {
      this.logger.error(`Unable kill ${suiteId}`);
    });
  }

  getTagList = function (tagsString) {
    let tags = JSON.parse(tagsString);
    tags = new Set(tags);
    return tags;
  };

  resultToClass(result): any {
    result = result.toUpperCase();
    let klass = "default";
    if (result === "FAILED") {
      klass = "danger";
    } else if (result === "PASSED") {
      klass = "success";
    } else if (result === "SKIPPED") {
      klass = "warning";
    } else if (result === "NOT_RUN") {
      klass = "default";
    } else if (result === "IN_PROGRESS") {
      klass = "info";
    } else if (result === "BLOCKED") {
      klass = "blocked";
    }
    return klass;
  }

  testClick(suiteExecutionId, suitePath) {
    this.reRunService.submitReRun(suiteExecutionId, suitePath);
  }

  requestedDaysToString(days) {
    let d = JSON.parse(days);
    let s = "";
    d.map(day => {
      s += day.charAt(0).toUpperCase() + day.charAt(1) + " ,";
    });
    s = s.replace(/,$/, "");
    return s;
  }

  getRequestedTime(hour, minute) {
    let s = "";
    if (hour < 10) {
      s += "0";
    }
    s += hour + ":";
    if (minute < 10) {
      s += "0";
    }
    s += minute;
    return s;
  }

  removeFilterButton(filterButton) {
    this.filterButtons = this.filterButtons.filter(x => x.filterKey !== filterButton.filterKey || x.filterValue !== filterButton.filterValue);
    let o = {};
    this.queryParameters = Object.keys(this.queryParameters).reduce((a, key) => {
      if (key !== filterButton.filterKey) {
        o[key] = this.queryParameters[key];
      }
      return o;
    }, {});
    this.router.navigate(['/regression'], {queryParams: this.prepareBaseQueryParams(null)});

  }

  onChangeAutoSchedule(checked, suiteExecution) {
    let enabled = checked;
    this.regressionService.disableAutoSchedule(suiteExecution.fields.execution_id, !checked).subscribe((response) => {
      if (!checked) {
        this.logger.success("Suite disabled");
      } else {
        this.logger.success("Suite enabled");
      }
    }, error => {
      this.logger.error("Unable to modify suite");
    })
  }

  toggleReRunOptions() {
    this.reRunOptionsReRunAll = !this.reRunOptionsReRunAll;
    this.reRunOptionsReRunFailed = !this.reRunOptionsReRunFailed;
  }

  togglereUseBuildImage() {
    this.reUseBuildImage = !this.reUseBuildImage;
  }

  onItemSelect(item: any) {
  }

  onSelectAll(items: any) {
  }

  get submitters() {
    return this.searchForm.get('submitters');
  }

  get suiteName() {
    return this.searchForm.get('suiteName');
  }

  onSubmit() {
    this.searching = false;
    let queryParams = [];
    if (this.searchForm.controls.suiteName.value != "") {
      queryParams.push({"suite_path": this.searchForm.controls.suiteName.value});
    }
    if (this.searchForm.controls.submitters.value != "") {
      queryParams.push({"submitter_email": this.searchForm.controls.submitters.value});
    }

    this.navigateByQueryParams(queryParams);
    this.searchForm.reset();
  }

  onCancel() {
    this.searching = false;
    this.searchForm.reset();
  }

  onSelectSuiteExecutionId() {
    this.searchForm.controls.submitters.setValue('');
    this.searchForm.controls.suiteName.setValue('');
  }

  onSearch() {
    if (this.searching == true){
      this.onCancel();
    }
    else {
      this.searching = true;
    }
  }

  executionReload() {
    let executionId = this.searchForm.get('executionId').value;
    if (this.searchingByExecutionId == true && !(executionId == "" || executionId == null)){
      window.open("/regression/suite_detail/" + executionId, '_blank');
    }

  }

  _flatten(items) {
    let itemString = '';
    for (let i = 0; i < items.length; ++i) {
      itemString += items[i];
      if (i != (items.length - 1)) {
        itemString += ',';
      }
    }
    return itemString;
  }


  suites() {
    return this.apiService.get("/regression/suites").pipe(switchMap((response) => {
      return of(response.data);
    }))
  }

  atLeastOneValidator(group: FormGroup): { [key: string]: boolean } | null {
    const submitters = group.get('submitters');
    const suiteName = group.get('suiteName');
    const searchByExecutionId = group.get('searchByExecutionId');
    const executionId = group.get('executionId');
    console.log(searchByExecutionId.value);
    if (((suiteName.value == "" || suiteName.value == null) && (submitters.value == "" || submitters.value == null)) && searchByExecutionId.value == false) {
      return {'atLeastOne': true};
    }
    else if (searchByExecutionId.value == true && (executionId.value == "" || executionId.value == null)){
      return {'atLeastOne': true};
    }
    return null;
  }

  onSuiteDetail(suiteId) {
    window.location.href = '/regression/suite_editor/' + suiteId;
  }

}
