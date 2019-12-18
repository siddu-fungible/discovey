import { Component, OnInit } from '@angular/core';
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";
import {RegressionService} from "../regression.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {ApiType} from "../../lib/api";
import {LoggerService} from "../../services/logger/logger.service";


@Component({
  selector: 'app-releases',
  templateUrl: './releases.component.html',
  styleUrls: ['./releases.component.css']
})
export class ReleasesComponent implements OnInit {
  releaseCatalogExecutions: ReleaseCatalogExecution [];
  byReleaseTrain: {[release_train: string]: {[description: string]: {}}} = {};
  jobStatusType: ApiType = new ApiType();
  constructor(private regressionService: RegressionService, private loggerService: LoggerService) { }
  driver: any = null;

  ngOnInit() {

    this.driver = of(true).pipe(switchMap(response => {
      return this.jobStatusType.get("/api/v1/regression/job_status_types");
    })).pipe(switchMap(response => {
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
    this.releaseCatalogExecutions.forEach(releaseCatalogExecution => {
      if (!this.byReleaseTrain.hasOwnProperty(releaseCatalogExecution.release_train)) {
        this.byReleaseTrain[releaseCatalogExecution.release_train] = {};
      }
      if (!this.byReleaseTrain[releaseCatalogExecution.release_train].hasOwnProperty(releaseCatalogExecution.description)) {
        this.byReleaseTrain[releaseCatalogExecution.release_train][releaseCatalogExecution.description] = {executions: [], master_execution: null};
      }

      this.byReleaseTrain[releaseCatalogExecution.release_train][releaseCatalogExecution.description]["executions"].push(releaseCatalogExecution);
      if (!releaseCatalogExecution.master_execution_id) {
        this.byReleaseTrain[releaseCatalogExecution.release_train][releaseCatalogExecution.description]["master_execution"] = releaseCatalogExecution;
      }

    });
    let i = 0;
  }

  refresh() {
    this.driver.subscribe(response => {

    }, error => {
      this.loggerService.error("refresh", error);
    });
  }

  onToggleRecurring(recurring, masterExecution) {
    masterExecution.recurring = recurring;
    masterExecution.update(masterExecution.getUrl({id: masterExecution.id})).subscribe(response => {

    }, error => {
      this.loggerService.error(`Unable to toggle recurring attribute`, error);
    })
  }

}
