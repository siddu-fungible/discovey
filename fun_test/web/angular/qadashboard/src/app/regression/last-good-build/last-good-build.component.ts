import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {switchMap} from "rxjs/operators";
import {ReleaseCatalogExecution} from "../release-catalogs/definitions";
import {LastGoodBuild} from "./definitions";
import {Observable, of} from "rxjs";
import {LoggerService} from "../../services/logger/logger.service";

@Component({
  selector: 'app-last-good-build',
  templateUrl: './last-good-build.component.html',
  styleUrls: ['./last-good-build.component.css']
})
export class LastGoodBuildComponent implements OnInit {
  driver: Observable<any> = null;
  lastGoodBuild: LastGoodBuild = new LastGoodBuild();
  constructor(private route: ActivatedRoute, private loggerService: LoggerService) { }
  buildMap: {[releaseTrain: string]: LastGoodBuild} = {};
  releaseTrainSet: Set<string> = new Set();
  ngOnInit() {

    this.driver = this.route.params.pipe(switchMap(params => {
      return this.lastGoodBuild.getAll();
    })).pipe(switchMap(builds => {
      builds.forEach(build => {
        this.releaseTrainSet.add(build.release_train);
        if (!this.buildMap.hasOwnProperty(build.release_train)) {
          this.buildMap[build.release_train] = build;
        }
      });
      return of(true);
    }));

    this.driver.subscribe(response => {

    }, error => {
      this.loggerService.error(`Unable to fetch last good build`, error);
    })

  }

  onBuildNumberChanged(buildNumber, releaseTrain) {
    this.lastGoodBuild.release_train = releaseTrain;
    this.lastGoodBuild.build_number = buildNumber;
    this.lastGoodBuild.update(this.lastGoodBuild.getUrl({release_train: releaseTrain})).subscribe(()=> {},error => {
      this.loggerService.error("Unable to update build number");
    })
  }

}
