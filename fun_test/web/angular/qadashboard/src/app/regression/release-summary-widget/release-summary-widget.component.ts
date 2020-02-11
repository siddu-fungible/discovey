import { Component, OnInit } from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of} from "rxjs";
import {LoggerService} from "../../services/logger/logger.service";
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";
import {last, switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {ApiType} from "../../lib/api";
import {LastGoodBuild} from "../last-good-build/definitions";

@Component({
  selector: 'app-release-summary-widget',
  templateUrl: './release-summary-widget.component.html',
  styleUrls: ['./release-summary-widget.component.css']
})
export class ReleaseSummaryWidgetComponent implements OnInit {
  driver: Observable<any> = null;
  constructor(private regressionService: RegressionService,
              private loggerService: LoggerService,
              private commonService: CommonService) { }
  releaseCatalogExecutions: ReleaseCatalogExecution [] = null;
  byReleaseTrain: {[releaseTrain: string]: any} = {};
  jobStatusTypes: ApiType = null;
  allBuildNumbers: number [] = [];
  lastGoodMap: {[releaseTrain: string]: any} = {};
  ngOnInit() {
    this.driver = of(true).pipe(switchMap(response => {
      return this.regressionService.getJobStatusTypes();
    })).pipe(switchMap(response => {
      this.jobStatusTypes = response;
      let rce = new ReleaseCatalogExecution();
      return rce.getAll();
    })).pipe(switchMap(response => {
      this.releaseCatalogExecutions = response;
      this.prepareByReleaseTrain();
      return of(true);
    }));
    this.refresh();
  }

  prepareByReleaseTrain() {
    let setOfBuildNumbers = new Set();
    this.releaseCatalogExecutions.forEach(releaseCatalogExecution => {
      if (!isNaN(releaseCatalogExecution.build_number)) {
        setOfBuildNumbers.add(releaseCatalogExecution.build_number);
        if (!this.byReleaseTrain.hasOwnProperty(releaseCatalogExecution.release_train)) {
          this.byReleaseTrain[releaseCatalogExecution.release_train] = {};
        }
        releaseCatalogExecution["started_date_string"] = this.commonService.getShortDateTimeFromEpoch(releaseCatalogExecution.started_date_timestamp);
        releaseCatalogExecution["completion_date_string"] = this.commonService.getShortDateTimeFromEpoch(releaseCatalogExecution.completion_date_timestamp);

        if (!this.byReleaseTrain[releaseCatalogExecution.release_train].hasOwnProperty(releaseCatalogExecution.description)) {
          this.byReleaseTrain[releaseCatalogExecution.release_train][releaseCatalogExecution.description] = {
            executions: [],
            master_execution: null
          };
          this.getLastGoodBuild(releaseCatalogExecution.release_train, this.byReleaseTrain[releaseCatalogExecution.release_train][releaseCatalogExecution.description]);
          this.lastGoodMap[releaseCatalogExecution.release_train] = null;
        }

        if (releaseCatalogExecution.state > this.jobStatusTypes["UNKNOWN"] && releaseCatalogExecution.state <= this.jobStatusTypes["COMPLETED"]) {
          this.byReleaseTrain[releaseCatalogExecution.release_train][releaseCatalogExecution.description]["executions"].push(releaseCatalogExecution);
        }
      }
    });
    this.allBuildNumbers = Array.from(setOfBuildNumbers).sort().reverse();
    let i = 0;
  }

  getLastGoodBuild(releaseTrain: string, key: string) {
    let lastGoodBuild = new LastGoodBuild();
    lastGoodBuild.get(lastGoodBuild.getUrl({release_train: releaseTrain})).subscribe(response => {
      this.lastGoodMap[releaseTrain] = lastGoodBuild.build_number;
    })
  }

  refresh() {
    this.driver.subscribe(response => {

    }, error => {
      this.loggerService.error(`Unable to initialize summary-widget`, error);
    })
  }

}
