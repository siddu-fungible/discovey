import { Component, OnInit } from '@angular/core';
import {SuiteEditorService, Suite} from "../suite-editor.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../../services/logger/logger.service";


@Component({
  selector: 'app-suites-view',
  templateUrl: './suites-view.component.html',
  styleUrls: ['./suites-view.component.css']
})
export class SuitesViewComponent implements OnInit {

  constructor(private service: SuiteEditorService, private loggerService: LoggerService) { }
  suites: Suite[] = null;
  availableCategories: string[] = null;
  selectedCategories: string[] = null;
  dropDownSettings = {};
  driver: Observable<any> = null;

  ngOnInit() {
    this.driver =
    of(true).pipe(switchMap(response => {
      return this.service.categories();
    })).pipe(switchMap(response => {
      this.availableCategories = response;
      return this.service.suites();
    })).pipe(switchMap(response => {
      this.suites = response;
      this.suites.map(suite => {
        suite["dirty"] = false;
        suite["originalCategories"] = suite.categories;
      });
      this.suites = this.suites.filter(suite => {
        let result = false;
        if (!this.selectedCategories || this.selectedCategories.length === 0) {
          result = true;
        } else if (this.selectedCategories.length > 0) {
          for (let index = 0; index < this.selectedCategories.length; index++) {
            if (suite.categories.indexOf(this.selectedCategories[index]) > -1) {
              result = true;
              break;
            }
          }
        }
        return result;
      });
      return of(true);
    }));
    this.refreshAll();

  }

  refreshAll() {
    this.driver.subscribe(response => {

    }, error=> {
      this.loggerService.error("Unable to initialize view component");
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
    this.refreshAll();
  }

}
