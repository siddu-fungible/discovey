import {Component, OnChanges, OnInit} from '@angular/core';
import {RegressionService} from "../regression.service";
import {forkJoin, Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../services/logger/logger.service";
import {ReleaseCatalog} from "../definitions";
import {Router} from "@angular/router";
import {slideInOutAnimation} from "../../animations/generic-animations";
import {Suite, SuiteEditorService} from "../suite-editor/suite-editor.service";
import {ReleaseCatalogExecution, ReleaseSuiteExecution} from "./definitions";
import {UserService} from "../../services/user/user.service";

@Component({
  selector: 'app-release-catalogs',
  templateUrl: './release-catalogs.component.html',
  styleUrls: ['./release-catalogs.component.css'],
  animations: [slideInOutAnimation]
})
export class ReleaseCatalogsComponent implements OnInit, OnChanges {
  driver: Observable<any> = null;
  releaseCatalogs: ReleaseCatalog[] = null;
  releaseCatalogExecution: ReleaseCatalogExecution = new ReleaseCatalogExecution();
  preparingCatalogExecution: boolean = false;
  selectedReleaseCatalog: ReleaseCatalog = null;
  users = null;
  selectedUser = null;
  releaseTrains: string [] = [];
  testBeds = null;
  status: string = null;
  constructor(private regressionService: RegressionService,
              private loggerService: LoggerService,
              private router: Router,
              private suiteEditorService: SuiteEditorService,
              private userService: UserService
  ) { }

  ngOnInit() {
    this.driver = of(true).pipe(switchMap(response => {
      return this.userService.users();
    })).pipe(switchMap(response => {
      this.users = response;
      this.status = "Fetching test-bed information";
      return this.regressionService.fetchTestbeds(true);
    })).pipe(switchMap(response => {
      this.testBeds = response;
      this.status = null;
      return this.regressionService.releaseTrains();
    })).pipe(switchMap(response => {
      this.releaseTrains = response;
      return this.regressionService.getReleaseCatalogs();
    })).pipe(switchMap(response => {
      this.releaseCatalogs = response;
      return of(true);
    }));
    this.refreshAll();
  }

  ngOnChanges() {
    this.refreshAll();
  }

  refreshAll() {
    this.driver.subscribe(response => {
    }, error => {
      this.loggerService.error("Unable to fetch release catalogs");
    })
  }

  removeCatalog(index) {
    if (confirm(`Are you sure, you want to remove ${this.releaseCatalogs[index].name}`)) {
      this.regressionService.deleteReleaseCatalog(this.releaseCatalogs[index].id).subscribe(response => {
        this.loggerService.success(`Removed catalog: ${this.releaseCatalogs[index].name}`);
        this.releaseCatalogs.splice(index, 1);
      }, error => {
        this.loggerService.error("Unable to remove catalog");
      })


    }
  }

  addACatalog() {
    this.router.navigate(['/regression/release_catalog_editor'])
  }

  editCatalog(catalogId) {
    this.router.navigate(['/regression/release_catalog_editor'], {queryParams: {id: catalogId}});
  }

  compareSuites(suiteA: Suite, suiteB: Suite) {
    let result: number = 0;
    if (suiteA.id > suiteB.id) {
      result = 1;
    } else if (suiteA.id < suiteB.id) {
      result = -1;
    }
    return result;
  }

  prepareRelease(index) {
    this.preparingCatalogExecution = true;
    this.selectedReleaseCatalog = this.releaseCatalogs[index];
    let allObservables = this.selectedReleaseCatalog.suites.map((suite) => {
      return this.suiteEditorService.suite(suite.id).pipe(switchMap(response => {
        this.releaseCatalogExecution.suiteExecutions.push(new ReleaseSuiteExecution({suite_id: suite.id, suite_details: response}));
        return of(true);
      }))});

    forkJoin(allObservables).subscribe(response => {
      //this.suitesForExecution.sort(this.compareSuites);
    }, error => {
      this.loggerService.error(`Unable to get suite ids`, error);
    });

  }

  createRelease() {
    if (!this.releaseCatalogExecution.owner) {
      return alert("Please select a user");
    }
    this.releaseCatalogExecution.release_catalog_id = this.selectedReleaseCatalog.id;
    this.releaseCatalogExecution.create(this.releaseCatalogExecution.url, this.releaseCatalogExecution.serialize()).subscribe(rceResponse => {
      this.loggerService.success(`Created catalog execution: ${rceResponse.id}`);
      this.router.navigateByUrl(`/regression/release_detail/${rceResponse.id}`);
    }, error => {
      this.loggerService.error(`Unable to execute catalog`, error);
    })
  }

  setExecutionDescription(description) {
    this.releaseCatalogExecution.description = description;
  }


}
