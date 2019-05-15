import {Component, Input, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {TriageService} from "../triage.service";
import {CommonService} from "../../services/common/common.service";
import {LoggerService} from "../../services/logger/logger.service";
import {ApiService} from "../../services/api/api.service";

@Component({
  selector: 'app-triage-detail',
  templateUrl: './triage-detail.component.html',
  styleUrls: ['./triage-detail.component.css']
})
export class TriageDetailComponent implements OnInit {
  @Input() triageId: number;
  triagingStateMap: any = null;
  triagingTrialStateMap: any = null;
  triage: any = null;
  trials: any = [];
  commits: any = [];
  commitMap: any = {};
  commitFetchStatus: string = null;

  constructor(private route: ActivatedRoute,
              private triageService: TriageService,
              private commonService: CommonService,
              private loggerService: LoggerService,
              private apiService: ApiService) { }

  ngOnInit() {
    this.route.params.pipe(switchMap((params) => {
      this.triageId = params['id'];
      return this.triageService.triagingStateToString();
    })).pipe(switchMap((triagingStateMap) => {
      this.triagingStateMap = triagingStateMap;
      return this.triageService.triagingTrialStateToString();
    })).pipe(switchMap((triagingTrialStateMap) => {
      this.triagingTrialStateMap = triagingTrialStateMap;
      return this.triageService.triages(this.triageId);
    })).pipe(switchMap( (triage) => {
      this.triage = triage;
      return this.triageService.trials(this.triageId, null);
    })).pipe(switchMap((trials) => {
      this.trials = trials;
      this.commitFetchStatus = "Fetching commit info";
      return this.getCommitsInBetween();
    })).pipe(switchMap(() => {
      return of(true);
    })).subscribe(() => {

    }, error => {
      this.loggerService.error(error);
    });

  }

  getCommitsInBetween() {
    return this.triageService.funOsCommits(this.triage.from_fun_os_sha, this.triage.to_fun_os_sha).pipe(switchMap((commits) => {
      this.commits = commits;
      this.commits.forEach((commit) => {
        this.commitMap[commit.sha] = {date: commit.date};
      });
      this.commitFetchStatus = null;
      return of(true);
    }));
  }

  getShortSha(sha) {
    return sha.substring(0, 7);
  }

  prettyTime(t) {
    let s = "";
    if (t) {
      s = this.commonService.getPrettyLocalizeTime(t);
    }
    return s;
  }

  startTriage() {
    let url = "/api/v1/triages/" + this.triageId;
    let payload = {"status": 20}; // INIT
    this.apiService.post(url, payload).subscribe((response) => {
      this.loggerService.success("Successully submitted start option");
    }, error => {
      this.loggerService.error("Error starting the triage");
    })
  }

  restartTrial(trial) {
    let url = "/api/v1/triages/" + trial.triage_id + "/trials/" + trial.fun_os_sha;
    let payload = {"status": 20};
    payload["tag"] = trial.tag + "_" + trial.tags.length;
    let tempArray = Array.from(trial.tags);
    tempArray.push(trial.tag);
    payload["tags"] = tempArray;
    this.apiService.post(url, payload).subscribe((response) => {
      this.loggerService.success("Trial re-start submitted");
    })
  }

}
