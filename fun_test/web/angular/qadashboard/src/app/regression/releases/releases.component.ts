import { Component, OnInit } from '@angular/core';
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";

@Component({
  selector: 'app-releases',
  templateUrl: './releases.component.html',
  styleUrls: ['./releases.component.css']
})
export class ReleasesComponent implements OnInit {
  releaseCatalogExecutions: ReleaseCatalogExecution [];
  constructor() { }

  ngOnInit() {
    let rce = new ReleaseCatalogExecution();
    rce.getAll().subscribe(response => {
      this.releaseCatalogExecutions = response;
    });
  }

}
