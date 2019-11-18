import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {LoggerService} from "../../services/logger/logger.service";
import {RegressionService} from "../regression.service";
import {Suite, SuiteEditorService} from "../suite-editor/suite-editor.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {showAnimation} from "../../animations/generic-animations";

@Component({
  selector: 'app-release-catalog-editor',
  templateUrl: './release-catalog-editor.component.html',
  styleUrls: ['./release-catalog-editor.component.css'],
  animations: [showAnimation]
})
export class ReleaseCatalogEditorComponent implements OnInit, OnChanges {
  driver: any = null;
  addingSuites: boolean = false;
  selectedSuites: Suite [] = [];
  selectedSuiteIds: number [] = [];
  constructor(private loggerService: LoggerService,
              private regressionService: RegressionService,
              private suiteEditorService: SuiteEditorService,
              private commonService: CommonService) { }

  ngOnInit() {
    console.log("Re-init release catalog");

  }

  ngOnChanges() {
    this.driver = of(true).pipe(switchMap(response => {
      this.suiteEditorService.suites();
      return of(true);
    }))
  }

  suitesSelectedByView(newlySelectedSuites) {
    console.log(newlySelectedSuites);
    this.addingSuites = false;
    this.addNewlySelectedSuites(newlySelectedSuites);
  }

  cancelSelection() {
    this.addingSuites = false;
  }

  addNewlySelectedSuites(newlySelectedSuites) {
    newlySelectedSuites.forEach(newlySelecteSuite => {
      if (this.selectedSuites.findIndex(selectedSuite => selectedSuite.id === newlySelecteSuite.id) < 0 ) {
        this.selectedSuites.push(newlySelecteSuite);
      }
    });
    this.selectedSuiteIds = [];
    this.selectedSuites.map(selectedSuite => {
      this.selectedSuiteIds.push(selectedSuite.id);
    });
    this.selectedSuiteIds = [...this.selectedSuiteIds];
  }

}
