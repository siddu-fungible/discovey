import {Component, OnInit} from '@angular/core';
import {SuiteEditorService, Suite} from "../suite-editor.service";
import {Observable, of, Subject} from "rxjs";
import {debounceTime, distinctUntilChanged, switchMap} from "rxjs/operators";
import {LoggerService} from "../../../services/logger/logger.service";
import {PagerService} from "../../../services/pager/pager.service";


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
  RECORDS_PER_PAGE: number = 20;
  currentPage = 1;
  pager: any = {};
  byNameSearchText: string = null;
  status: string = null;


  constructor(private service: SuiteEditorService, private loggerService: LoggerService, private pagerService: PagerService) {



  }


  ngOnInit() {
    this.driver =
      of(true).pipe(switchMap(response => {
        return this.service.categories();
      })).pipe(switchMap(response => {
        this.availableCategories = response;
        return this.service.suites<number>(true, this.RECORDS_PER_PAGE, this.currentPage, this.selectedCategories, this.byNameSearchText);
      })).pipe(switchMap(suiteCount => {
        this.suitesCount = suiteCount;
        this.pager = this.pagerService.getPager(this.suitesCount, this.currentPage, this.RECORDS_PER_PAGE);
        return this.service.suites<Suite[]>(null, this.RECORDS_PER_PAGE, this.currentPage, this.selectedCategories, this.byNameSearchText);
      })).pipe(switchMap(response => {
        this.suites = response;
        this.suites.map(suite => {
          suite["dirty"] = false;
          suite["originalCategories"] = suite.categories;
        });
        return of(true);
      }));
    this.refreshAll();

  }

  setPage(page) {
    if (page === 0 || (page > this.pager.endPage)) {
      return;
    }
    this.currentPage = page;
    this.refreshAll();
  }

  refreshAll() {
    this.status = "Refreshing suites";
    console.log(this.status);
    this.driver.subscribe(response => {
      this.status = null;
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
    this.setPage(1);
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
    this.refreshAll();
  }




}
