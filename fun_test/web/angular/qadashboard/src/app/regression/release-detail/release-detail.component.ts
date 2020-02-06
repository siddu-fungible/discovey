import { Component, OnInit } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {switchMap} from "rxjs/operators";
import {concat, Observable, of} from "rxjs";
import {LoggerService} from "../../services/logger/logger.service";
import {RegressionService} from "../regression.service";
import {ReleaseCatalogExecution, ReleaseSuiteExecution} from "../release-catalogs/definitions";
import {Suite, SuiteEditorService} from "../suite-editor/suite-editor.service";
import {showAnimation} from "../../animations/generic-animations";
import {ApiType} from "../../lib/api";
import {ButtonType, FunActionLink, FunButtonWithIcon} from "../../ui-elements/definitions";
import {SuiteExecutions} from "../definitions";

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
  modifyingTestBed: boolean = false;
  newTestBedName: string = null;
  testBeds = [];
  addingSuites: boolean = false;
  headerLeftAlignedButtons: FunButtonWithIcon [] = [];
  suitesHeaderActionLinks: FunActionLink [] = [];
  suitesHeaderLeftAlignedButtons: FunButtonWithIcon [] = [];
  suitesDeleteButton: FunButtonWithIcon = null;
  gotoMasterButton: FunButtonWithIcon = null;
  addSuitesLinkObject: FunActionLink = null;
  headerSubText1: string = "";

  suiteMap: {[suite_id: number]: Suite} = {};
  atLeastOneSelected: boolean = false;
  jobStatusTypes: ApiType = null;
  constructor(private route: ActivatedRoute,
              private logger: LoggerService,
              private regressionService: RegressionService,
              private suiteEditorService: SuiteEditorService,
              private router: Router) {

    //console.log(ButtonType.DELETE);
    this.headerLeftAlignedButtons.push(new FunButtonWithIcon({type: ButtonType.DELETE,
      text: "delete this instance", callback: this.deleteRelease.bind(this)}));

    this.addSuitesLinkObject = new FunActionLink({text: "+ Add suites",
      callback: this.addSuites.bind(this)});
    this.suitesHeaderActionLinks.push(this.addSuitesLinkObject);
    this.suitesDeleteButton = new FunButtonWithIcon({type: ButtonType.DELETE, text: "delete suite(s)", callback: this.deleteSuites.bind(this), show: false});
    this.suitesHeaderLeftAlignedButtons.push(this.suitesDeleteButton);
  }
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
      return this.regressionService.getJobStatusTypes();
    })).pipe(switchMap(response => {
      this.jobStatusTypes = response;
      this.status = "Fetching catalog execution";
      this.releaseCatalogExecution = new ReleaseCatalogExecution();
      return this.releaseCatalogExecution.get(this.releaseCatalogExecution.getUrl({id: this.executionId}));
    })).pipe(switchMap(response => {
      this.headerSubText1 = `Release-train: ${this.releaseCatalogExecution.release_train}`;
      if (this.releaseCatalogExecution.build_number) {
        this.headerSubText1 += `, Build: ${this.releaseCatalogExecution.build_number}`;
      }

      if (this.releaseCatalogExecution.master_execution_id) {
        this.headerLeftAlignedButtons.push(new FunButtonWithIcon({type: ButtonType.LINK,
      text: "go to master instance",
      callback: this.gotoMaster.bind(this)}));
      }
      this.fetchSuiteDetails();
      this.status = null;
      return this.regressionService.fetchTestbeds(true);
    })).pipe(switchMap(response => {
      this.testBeds = response;
      return of(true);
    }));

    this.refresh();
  }

  fetchSuiteDetails() {
    if (this.releaseCatalogExecution.suite_executions) {
      let allObservables: Observable <any>[] = this.releaseCatalogExecution.suite_executions.map(suiteExecution => {

        if (!this.suiteMap.hasOwnProperty(suiteExecution.suite_id)) {
          return this.suiteEditorService.suite(suiteExecution.suite_id).pipe(switchMap(response => {
            let newSuite: Suite = new Suite(response);
            suiteExecution.suite_details = newSuite;
            this.suiteMap[newSuite.id] = newSuite;
            return of(true);
          }));

        } else {
          suiteExecution.suite_details = this.suiteMap[suiteExecution.suite_id];
          return of(true);
        }


      });

      concat(...allObservables).subscribe(response => {
        this.fetchJobState();
      }, error => {
        this.logger.error(`Unable to fetch suite information`, error);
      })
    }
  }

  fetchJobState() {
    if (this.releaseCatalogExecution.suite_executions) {
      let allObservables: Observable <any>[] = this.releaseCatalogExecution.suite_executions.map(suiteExecution => {
        if (suiteExecution.job_id) {
          let suiteExecutionObject: SuiteExecutions = new SuiteExecutions();
          return suiteExecutionObject.get(suiteExecutionObject.getUrl({execution_id: suiteExecution.job_id})).pipe(switchMap(response => {
            suiteExecution.job_status = response[0].state;
            suiteExecution.job_result = response[0].result;
            return of(true);
          }))
        } else {
          return of(true);
        }

      });

      concat(...allObservables).subscribe(response => {

      }, error => {
        this.logger.error(`Unable to fetch suite information`, error);
      })
    }
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
    this.releaseCatalogExecution.update(this.releaseCatalogExecution.getUrl({id: this.executionId})).subscribe(response => {
      this.fetchSuiteDetails();
    }, error => {
      this.logger.error(`release-detail`, error);
    });

  }

  onSubmitModifyTestBed(suiteExecution) {
    suiteExecution.test_bed_name = this.newTestBedName;
    let originalSuiteExecutions = this.releaseCatalogExecution.suite_executions;
    this.releaseCatalogExecution.update(this.releaseCatalogExecution.getUrl({id: this.executionId})).subscribe(response => {
      suiteExecution.modifyingTestBed = false;
      this.releaseCatalogExecution.suite_executions = originalSuiteExecutions;
    }, error => {
      this.logger.error(`release-detail`, error);
      suiteExecution.modifyingTestBed = false;

    });
  }

  onCancelModifyTestBed(suiteExecution) {
    suiteExecution.modifyingTestBed = false;
  }


  suitesSelectedByView(newlySelectedSuites) {
    let originalSuiteExecutions = this.releaseCatalogExecution.suite_executions;
    newlySelectedSuites.forEach(newlySelectedSuite => {
      if (!this.releaseCatalogExecution.suite_executions) {
        this.releaseCatalogExecution.suite_executions = [];
      }
      this.releaseCatalogExecution.suite_executions.push(new ReleaseSuiteExecution({suite_id: newlySelectedSuite.id, test_bed_name: null, suite_details: newlySelectedSuite}))
    });
    this.releaseCatalogExecution.update(this.releaseCatalogExecution.getUrl({id: this.releaseCatalogExecution.id})).subscribe(() => {
      this.addingSuites = false;
      this.fetchSuiteDetails();
    }, error => {
      this.logger.error(`Unable to add suites`, error);
    })
  }

  cancelSuiteSelection() {
    this.addingSuites = false;
    this.addSuitesLinkObject.show = true;

  }

  checkAtLeastOneSelected() {
    setTimeout(() => {
      this.atLeastOneSelected = false;
      this.suitesDeleteButton.show = false;
      for (let index = 0; index < this.releaseCatalogExecution.suite_executions.length; index++) {
        if (this.releaseCatalogExecution.suite_executions[index].selected) {
          this.atLeastOneSelected = true;
          this.suitesDeleteButton.show = true;
          break;
        }
      }
    }, 1);
  }

  onSelectClicked() {
    this.checkAtLeastOneSelected();
  }

  deleteSuites() {
    if(confirm("Are you sure you want to delete suite(s)?")) {
      this.releaseCatalogExecution.suite_executions = this.releaseCatalogExecution.suite_executions.filter(suite_execution => !suite_execution.selected);
      this.releaseCatalogExecution.update(this.releaseCatalogExecution.getUrl({id: this.releaseCatalogExecution.id})).subscribe(() => {
        this.checkAtLeastOneSelected();
        this.fetchSuiteDetails();
        this.suitesDeleteButton.show = false;
      }, error => {
        this.logger.error(`Unable to delete suite(s)`, error);
      })
    }
  }

  gotoMaster() {
    window.location.href = '/regression/release_detail/' + this.releaseCatalogExecution.master_execution_id;
  }

  execute() {
    this.releaseCatalogExecution.ready_for_execution = true;
    this.releaseCatalogExecution.update(this.releaseCatalogExecution.getUrl({id: this.releaseCatalogExecution.id})).subscribe(response => {
      this.fetchSuiteDetails();
    }, error => {
      this.logger.error(`Unable to submit request for execution`, error);
    })

  }

  deleteRelease() {
    //console.log("Delete release");
    if (confirm('Are you sure you want to delete this release?')) {
      this.releaseCatalogExecution.delete(this.releaseCatalogExecution.getUrl({id: this.releaseCatalogExecution.id})).subscribe(response => {
        this.router.navigateByUrl('/regression/releases');
      }, error => {
        this.logger.error(`Unable to delete release`, error);
      })

    }
  }

  addSuites(linkObject) {
    this.addSuitesLinkObject.show = false;
    this.addingSuites = true;
  }

  test() {
    console.log(this.releaseCatalogExecution);
  }
  /*
  reRunSuiteExecution(suiteExecution) {
    this.releaseCatalogExecution.reRunRequest(suiteExecution);
  }*/

  reRunRequest(suiteExecution) {
    let url = this.releaseCatalogExecution.getUrl({id: this.releaseCatalogExecution.id});
    suiteExecution.re_run_request = true;
    this.releaseCatalogExecution.update(url).subscribe(response => {
      this.fetchSuiteDetails();
    }, error => {
      this.logger.error(`Unable to re-run`, error);
    })
  }

  updateLastGoodBuild() {
    let url = this.releaseCatalogExecution.getUrl({id: this.releaseCatalogExecution.id});
    this.releaseCatalogExecution.update_last_good_build = !this.releaseCatalogExecution.update_last_good_build;
    this.releaseCatalogExecution.update(url).subscribe(response => {

    }, error => {
      this.logger.error(`Unable to update last-good build`, error);
    })
  }

}
