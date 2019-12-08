import { Component, OnInit } from '@angular/core';
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";
import {RegressionService} from "../regression.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";

@Component({
  selector: 'app-releases',
  templateUrl: './releases.component.html',
  styleUrls: ['./releases.component.css']
})
export class ReleasesComponent implements OnInit {
  releaseCatalogExecutions: ReleaseCatalogExecution [];
  constructor(private regressionService: RegressionService) { }
  driver: any = null;

  ngOnInit() {

    this.driver = of(true).pipe(switchMap(response => {
      let rce = new ReleaseCatalogExecution();
      return rce.getAll().subscribe(response => {
        this.releaseCatalogExecutions = response;
      });
    }))
  }

  refresh() {
    this.driver.subscribe(response => {

    });
  }


}
