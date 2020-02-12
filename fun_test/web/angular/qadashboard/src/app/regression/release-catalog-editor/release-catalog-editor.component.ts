import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {LoggerService} from "../../services/logger/logger.service";
import {Suite, SuiteEditorService} from "../suite-editor/suite-editor.service";
import {of} from "rxjs";
import {catchError, switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {showAnimation} from "../../animations/generic-animations";
import {ReleaseCatalogSuite, ReleaseCatalog} from "../definitions";
import {RegressionService} from "../regression.service";
import { Location } from '@angular/common';

@Component({
  selector: 'app-release-catalog-editor',
  templateUrl: './release-catalog-editor.component.html',
  styleUrls: ['./release-catalog-editor.component.css'],
  animations: [showAnimation]
})
export class ReleaseCatalogEditorComponent implements OnInit, OnChanges {
  catalogId: number = null;
  driver: any = null;
  addingSuites: boolean = false;
  selectedSuiteIds: number [] = [];
  suites: {[id: number]: Suite} = {};
  changeDetected: boolean = false;
  releaseCatalog: ReleaseCatalog = null; //= new ReleaseCatalog();
  sectionTitle: string = "Creating a new release catalog";
  queryParams: any = {};

  constructor(private loggerService: LoggerService,
              private regressionService: RegressionService,
              private suiteEditorService: SuiteEditorService,
              private commonService: CommonService,
              private location: Location) {

    this.driver = of(true).pipe(switchMap(response => {
      return this.commonService.getRouterQueryParam();
    })).pipe(switchMap(response => {
      this.queryParams = response;
      if (this.queryParams.hasOwnProperty("id")) {
        this.catalogId = parseInt(this.queryParams.id);
      }
      if (this.catalogId) {
        this.sectionTitle = "Editing release catalog";
        return this.regressionService.getReleaseCatalog(this.catalogId);
      } else {
        return of(new ReleaseCatalog());
      }
    })).pipe(switchMap(response => {
      this.releaseCatalog = response;
      this.setSelectedSuiteIds();
      this.fetchSuites();
      return of(true);
    }), catchError(error => {
      throw error;
    }))
  }

  fetchSuites() {
    if (this.releaseCatalog.hasOwnProperty("suites")) {
      this.releaseCatalog.suites.forEach(suite => {
        if (!this.suites.hasOwnProperty(suite.id)) {
          this.suiteEditorService.suite(suite.id).subscribe(response => {
            this.suites[suite.id] = response;
          })
        }

      })
    }
  }

  ngOnInit() {
    console.log("Re-init release catalog");
    this.refreshAll();
  }

  ngOnChanges() {
    //this.refreshAll();
  }

  refreshAll() {
    this.driver.subscribe(response => {

    }, error => {
      this.loggerService.error("Unable to initialize release catalog");
    })
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
        this.changeDetected = true;
      }

      if (!this.suites.hasOwnProperty(newlySelecteSuite.id)) {
        this.suites[newlySelecteSuite.id] = newlySelecteSuite;
      }
    });
    this.setSelectedSuiteIds();
  }

  setSelectedSuiteIds() {
    this.selectedSuiteIds = [];
    this.releaseCatalog.suites.map(selectedSuite => {
      this.selectedSuiteIds.push(selectedSuite.id);
    });
    this.selectedSuiteIds = [...this.selectedSuiteIds];
  }

  catalogNameChanged(name) {
    if (name !== this.releaseCatalog.name) {
      this.releaseCatalog.name = name;
      this.changeDetected = true;
    }
  }

  catalogDescriptionChanged(description) {
    if (description !== this.releaseCatalog.description) {
      this.releaseCatalog.description = description;
      this.changeDetected = true;
    }
  }

  submitClick() {
    if (!this.catalogId) {
      this.regressionService.createReleaseCatalog(this.releaseCatalog).subscribe(response => {
        this.loggerService.success("Submitted release catalog");
        this.changeDetected = false;
        this.location.back();
      }, error => {
        this.loggerService.error("Unable to submit release catalog");
      })
    } else {
      this.regressionService.updateReleaseCatalog(this.catalogId, this.releaseCatalog).subscribe(response => {
        this.loggerService.success("Updated release catalog");
        this.changeDetected = false;
      }, error => {
        this.loggerService.error("Unable to update release catalog");
      })
    }

  }

  /*
  updateReleaseCatalog(silent: boolean = false) {
    this.regressionService.updateReleaseCatalog(this.catalogId, this.releaseCatalog).subscribe(response => {
      this.loggerService.
    })
  }*/

  back() {
    this.location.back();
  }

  removeSelectedSuite(index) {
    this.releaseCatalog.suites.splice(index, 1);
    this.changeDetected = true;
  }

}
