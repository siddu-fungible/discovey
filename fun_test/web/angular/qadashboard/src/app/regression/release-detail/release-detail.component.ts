import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {LoggerService} from "../../services/logger/logger.service";
import {RegressionService} from "../regression.service";
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";

@Component({
  selector: 'app-release-detail',
  templateUrl: './release-detail.component.html',
  styleUrls: ['./release-detail.component.css']
})
export class ReleaseDetailComponent implements OnInit {
  executionId: number = null;
  constructor(private route: ActivatedRoute,
              private logger: LoggerService,
              private regressionService: RegressionService) { }
  driver: any = null;
  releaseCatalogExecution: ReleaseCatalogExecution = new ReleaseCatalogExecution();

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['executionId']) {
        this.executionId = params['executionId'];
      }
    });
    this.driver = this.route.params.pipe(switchMap(params => {
      if (params['executionId']) {
        this.executionId = params.executionId;
      }
      return this.releaseCatalogExecution.get(this.releaseCatalogExecution.getUrl({execution_id: this.executionId}));
    })).pipe(switchMap(response => {
      return of(true)
    })).pipe(switchMap(response => {
      return of(true);
    }));

    this.refresh();
  }

  refresh() {
    this.driver.subscribe(response => {

    }, error => {
      this.logger.error(`release-detail`, error);
    })
  }

}