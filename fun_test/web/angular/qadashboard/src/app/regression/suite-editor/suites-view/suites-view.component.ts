import {Component, Input, OnInit, EventEmitter, Output} from '@angular/core';
import {SuiteEditorService, Suite} from "../suite-editor.service";
import {Observable, of, Subject} from "rxjs";
import {debounceTime, distinctUntilChanged, switchMap} from "rxjs/operators";
import {LoggerService} from "../../../services/logger/logger.service";
import {PagerService} from "../../../services/pager/pager.service";
import {ActivatedRoute, Router} from "@angular/router";


enum Mode {
  DEFAULT = 0,
  SELECTION = 1
}

@Component({
  selector: 'app-suites-view',
  templateUrl: './suites-view.component.html',
  styleUrls: ['./suites-view.component.css']
})
export class SuitesViewComponent implements OnInit {
  suites: Suite[] = null;
  availableCategories: string[] = null;
  selectedCategories: string[] = null;
  dropDownSettings = {};
  driver: Observable<any> = null;
  suitesCount: number = null;
  DEFAULT_RECORDS_PER_PAGE: number = 40;
  recordsPerPage: number = 40;
  currentPage = 1;
  pager: any = {};
  byNameSearchText: string = null;
  status: string = null;
  @Input() multiSelect: boolean = false;
  @Input() selectedSuiteIds: number [] = [];
  @Output() reportSelectedSuites = new EventEmitter<Suite []>();
  @Output() cancelSelection = new EventEmitter();
  Mode = Mode;
  mode: Mode = Mode.DEFAULT;
  showScriptPath: boolean = true;
  showAllSuites: boolean = false;
  ownerEmail: string = null;

  constructor(private service: SuiteEditorService, private loggerService: LoggerService, private pagerService: PagerService,
              private router: Router, private route: ActivatedRoute) {
    this.recordsPerPage = this.DEFAULT_RECORDS_PER_PAGE;

  }


  ngOnInit() {
    if (this.multiSelect) {
      this.mode = Mode.SELECTION;
      this.recordsPerPage = 5;
    }
    this.driver =
      of(true).pipe(switchMap(response => {
        return this.getQueryParam();
      })).pipe(switchMap(response => {
        return this.service.categories();
      })).pipe(switchMap(response => {
        this.availableCategories = response;
        return this.service.suites<number>(true, this.recordsPerPage, this.currentPage, this.selectedCategories, this.byNameSearchText);
      })).pipe(switchMap(suiteCount => {
        this.suitesCount = suiteCount;
        this.pager = this.pagerService.getPager(this.suitesCount, this.currentPage, this.recordsPerPage);
        return this.service.suites<Suite[]>(null, this.recordsPerPage, this.currentPage, this.selectedCategories, this.byNameSearchText, this.ownerEmail);
      })).pipe(switchMap((response: Suite []) => {
        //console.log(typeof response);
        //console.log(Object.prototype.toString.call(response[0]));
        //response[0].p();
        this.suites = response;
        this.suites.map(suite => {
          suite["dirty"] = false;
          suite["originalCategories"] = suite.categories;
          if (this.selectedSuiteIds.indexOf(suite.id) > -1) {
            suite.selected = true;
          }
        });
        return of(true);
      }));
    this.refreshAll();

  }

  setPage(page) {
    if (page === 0 || (page > this.pager.totalPages)) {
      return;
    }
    this.currentPage = page;
    this.refreshAll();
  }

  cloneSuite(id) {
    let url = "/regression/suite_editor?clone_id=" + String(id);
    this.router.navigateByUrl(url);
  }

  refreshAll() {
    this.status = "Refreshing suites";
    console.log(this.status);
    this.driver.subscribe(response => {
      this.status = null;
      //this.setPage(this.currentPage);
    }, error => {
      this.loggerService.error("Unable to initialize view component");
      this.status = null;

    })
  }

  onSubmitCategories(suite) {
    this.service.replace(suite, suite.id).subscribe(response => {
      suite.dirty = false;
      suite.originalCategories = suite.categories;
    }, error => {
      this.loggerService.error("Unable to update suite");
    })
  }

  onDismissCategories(suite) {
    suite.categories = suite.originalCategories;
    suite.dirty = false;
  }

  onChangeSelectedCategories() {
    console.log(this.selectedCategories);
    //this.setPage(1);
    this.refreshAll();
  }

  onShortDescriptionChangedEvent(shortDescription, suite) {
    suite.short_description = shortDescription;
    this.service.replace(suite, suite.id).subscribe(() => {
      this.loggerService.success("Updated short description");
    }, error => {
      this.loggerService.error("Unable to update short description");
    })
  }

  onSearchText(searchText) {
    this.byNameSearchText = searchText;
    //console.log(this.byNameSearchText);
    this.currentPage = 1;
    this.refreshAll();
    //this.setPage(1);
  }

  onAddSuiteClick() {
    window.location.href = "/regression/suite_editor";
  }


  onDeleteSuite(suite) {
    if (confirm(`Are you sure, you want to delete ${suite.name}`)) {
      this.service.delete(suite).subscribe(response => {
        this.loggerService.success(`Suite ${suite.name} deleted`);
        this.refreshAll();
      }, error => {
        this.loggerService.error("Unable to delete suite");
      })
    }
  }

  onSubmitClick() {
    this.reportSelectedSuites.emit(this.suites.filter(suite => suite.selected));
  }

  onCancelClick() {
    this.cancelSelection.emit();
  }

  showAllSuitesClick() {
    this.showAllSuites = !this.showAllSuites;
    if (!this.showAllSuites) {
      this.recordsPerPage = this.DEFAULT_RECORDS_PER_PAGE;
    } else {
      this.recordsPerPage = this.suitesCount;
    }
    this.refreshAll();
  }

   getQueryParam() {
    return this.route.queryParams.pipe(switchMap(params => {
      if (params.hasOwnProperty('owner_email')) {
        this.ownerEmail = params["owner_email"]
      }
      return of(params);
    }))
  }
}
