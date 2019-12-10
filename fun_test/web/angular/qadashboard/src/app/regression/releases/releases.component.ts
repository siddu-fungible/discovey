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
      return of(true);
    }));

    this.refresh();
  }

  refresh() {
    this.driver.subscribe(response => {

    }, error => {
      this.loggerService.error("refresh", error);
    });
  }


}
