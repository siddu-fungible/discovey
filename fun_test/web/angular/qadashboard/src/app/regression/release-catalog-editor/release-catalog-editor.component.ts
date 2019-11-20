import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {LoggerService} from "../../services/logger/logger.service";
import {Suite, SuiteEditorService} from "../suite-editor/suite-editor.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {showAnimation} from "../../animations/generic-animations";
import {ReleaseCatalogSuite, ReleaseCatalog} from "../declarations";
import {RegressionService} from "../regression.service";
import { Location } from '@angular/common';

@Component({
  selector: 'app-release-catalog-editor',
  templateUrl: './release-catalog-editor.component.html',
  styleUrls: ['./release-catalog-editor.component.css'],
  animations: [showAnimation]
})
export class ReleaseCatalogEditorComponent implements OnInit, OnChanges {
  driver: any = null;
  addingSuites: boolean = false;
  //selectedSuites: Suite [] = [];
  selectedSuiteIds: number [] = [];
  suites: {[id: number]: Suite} = {};
  constructor(private loggerService: LoggerService,
              private regressionService: RegressionService,
              private suiteEditorService: SuiteEditorService,
              private commonService: CommonService,
              private location: Location) { }

  releaseCatalog: ReleaseCatalog = new ReleaseCatalog();

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
      if (this.releaseCatalog.suites.findIndex(selectedSuite => selectedSuite.id === newlySelecteSuite.id) < 0 ) {
        this.releaseCatalog.suites.push(new ReleaseCatalogSuite(newlySelecteSuite.id));
      }

      if (!this.suites.hasOwnProperty(newlySelecteSuite.id)) {
        this.suites[newlySelecteSuite.id] = newlySelecteSuite;
      }
    });
    this.selectedSuiteIds = [];
    this.releaseCatalog.suites.map(selectedSuite => {
      this.selectedSuiteIds.push(selectedSuite.id);
    });
    this.selectedSuiteIds = [...this.selectedSuiteIds];
  }

  catalogNameChanged(name) {

  }

  submitClick() {
    this.regressionService.createReleaseCatalog(this.releaseCatalog).subscribe(response => {
      this.loggerService.success("Submitted release catalog");
    }, error => {
      this.loggerService.error("Unable to submit release catalog");
    })
  }

  back() {
    this.location.back();
  }

}
