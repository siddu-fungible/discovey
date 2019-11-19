import {Component, OnChanges, OnInit} from '@angular/core';
import {RegressionService} from "../regression.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {LoggerService} from "../../services/logger/logger.service";
import {ReleaseCatalog} from "../declarations";

@Component({
  selector: 'app-release-catalogs',
  templateUrl: './release-catalogs.component.html',
  styleUrls: ['./release-catalogs.component.css']
})
export class ReleaseCatalogsComponent implements OnInit, OnChanges {
  driver: Observable<any> = null;
  releaseCatalogs: ReleaseCatalog[] = null;
  constructor(private regressionService: RegressionService, private  loggerService: LoggerService) { }

  ngOnInit() {
    this.driver = of(true).pipe(switchMap(response => {
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
      this.releaseCatalogs = this.releaseCatalogs.splice(index, 1);
    }
  }
}
