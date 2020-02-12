import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {switchMap} from "rxjs/operators";
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";
import {LastGoodBuild} from "./definitions";
import {Observable} from "rxjs";
import {LoggerService} from "../../services/logger/logger.service";

@Component({
  selector: 'app-last-good-build',
  templateUrl: './last-good-build.component.html',
  styleUrls: ['./last-good-build.component.css']
})
export class LastGoodBuildComponent implements OnInit {
  driver: Observable<any> = null;
  releaseTrain: string = null;
  lastGoodBuild: LastGoodBuild = new LastGoodBuild();
  constructor(private route: ActivatedRoute, private loggerService: LoggerService) { }

  ngOnInit() {

    this.driver = this.route.params.pipe(switchMap(params => {
      if (params['releaseTrain']) {
        this.releaseTrain = params.releaseTrain;
      }
      return this.lastGoodBuild.get(this.lastGoodBuild.getUrl({release_train: this.releaseTrain}));
    }));

    this.driver.subscribe(response => {

    }, error => {
      this.loggerService.error(`Unable to fetch last good build`, error);
    })

  }

}
