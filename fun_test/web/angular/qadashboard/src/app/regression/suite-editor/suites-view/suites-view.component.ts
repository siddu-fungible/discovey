import { Component, OnInit } from '@angular/core';
import {SuiteEditorService, Suite} from "../suite-editor.service";
import {of} from "rxjs";
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
  dropDownSettings = {};

  ngOnInit() {
    of(true).pipe(switchMap(() => {
      return this.service.suites();
    })).pipe(switchMap(response => {
      this.suites = response;
      this.suites.map(suite => {
        suite["dirty"] = false;
        suite["originalCategories"] = suite.categories;
      });
      return this.service.categories();
    })).subscribe(response => {
      this.availableCategories = response;
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

}
