import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {switchMap} from "rxjs/operators";
import {concat, Observable, of} from "rxjs";
import {LoggerService} from "../../services/logger/logger.service";
import {RegressionService} from "../regression.service";
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";
import {Suite, SuiteEditorService} from "../suite-editor/suite-editor.service";
import {showAnimation} from "../../animations/generic-animations";

@Component({
  selector: 'app-release-detail',
  templateUrl: './release-detail.component.html',
  styleUrls: ['./release-detail.component.css'],
  animations: [showAnimation]
})
export class ReleaseDetailComponent implements OnInit {
  executionId: number = null;
  status: string = null;
  editing: boolean = false;
  showingScripts: boolean = false;
  constructor(private route: ActivatedRoute,
              private logger: LoggerService,
              private regressionService: RegressionService,
              private suiteEditorService: SuiteEditorService) { }
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
      this.status = "Fetching catalog execution";
      return this.releaseCatalogExecution.get(this.releaseCatalogExecution.getUrl({execution_id: this.executionId}));
    })).pipe(switchMap(response => {
      this.fetchSuiteDetails();
      this.status = null;
      return of(true)
    })).pipe(switchMap(response => {
      return of(true);
    }));

    this.refresh();
  }

  fetchSuiteDetails() {
    let allObservables: Observable <boolean>[] = this.releaseCatalogExecution.suite_executions.map(suiteExecution => this.suiteEditorService.suite(suiteExecution.suite_id).pipe(switchMap(response => {
      suiteExecution.suite_details = new Suite(response);
      return of(true);
    })));

    concat(...allObservables).subscribe(response => {

    }, error => {
      this.logger.error(`Unable to fetch suite information`, error);
    })

  }
  refresh() {
    this.driver.subscribe(response => {

    }, error => {
      this.logger.error(`release-detail`, error);
    })
  }

  descriptionChangedCallback(newDescription) {
    let originalDescription = this.releaseCatalogExecution.description;
    this.releaseCatalogExecution.description = newDescription;
    this.releaseCatalogExecution.update(this.releaseCatalogExecution.getUrl({execution_id: this.executionId})).subscribe(response => {

    }, error => {
      this.logger.error(`release-detail`, error);
    });

  }



}
