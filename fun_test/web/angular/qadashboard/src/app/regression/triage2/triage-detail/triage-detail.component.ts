import {Component, Input, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {TriageService} from "../triage.service";
import {CommonService} from "../../../services/common/common.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {ApiService} from "../../../services/api/api.service";
import {Title} from "@angular/platform-browser";

class CommitNode {
  funOsSha: string;
  date: string;
  jenkinsBuildNumber: number;
  lsfJobId: number;
  status: number;
  selectedForTrial: boolean = false;
  tag: string;
  regexMatch: string;
  trialSetId: number;
  triageId: number;
  trial: any;
  selected: boolean = false;
  result: string;
  id: number;
  originalId: number;
  active: boolean = true;
  reruns: boolean = false;
  submissionDateTime: any = null;
  showReruns: boolean = false;
}


@Component({
  selector: 'app-triage-detail',
  templateUrl: './triage-detail.component.html',
  styleUrls: ['./triage-detail.component.css']
})
export class TriageDetailComponent implements OnInit {
  @Input() triageId: number;
  triagingStateMap: any = null;
  triagingTrialStateMap: any = null;
  triagingStringToCodeMap = {};
  triage: any = null;
  trials: any = [];
  commits: CommitNode [] = [];
  commitMap: any = {};
  commitFetchStatus: string = null;
  showAll: boolean = true;  // Show all potential git commits
  reRuns: any = null;
  currentRerunCommit: any = null;

  FUN_OS_GITHUB_BASE_URL = "https://github.com/fungible-inc/FunOS/commit/";

  constructor(private route: ActivatedRoute,
              private triageService: TriageService,
              private commonService: CommonService,
              private loggerService: LoggerService,
              private apiService: ApiService, private title: Title) {
  }

  ngOnInit() {
    this.title.setTitle("Regression Finder");
    this.route.params.pipe(switchMap((params) => {
      this.triageId = params['id'];
      return this.triageService.triagingStateToString();
    })).pipe(switchMap((triagingStateMap) => {
      this.triagingStateMap = triagingStateMap;
      return this.triageService.triagingTrialStateToString();
    })).pipe(switchMap((triagingTrialStateMap) => {
      this.triagingTrialStateMap = triagingTrialStateMap;
      for (let key of Object.keys(this.triagingStateMap)) {
        this.triagingStringToCodeMap[this.triagingStateMap[key]] = key;
      }
      return of(this.triageId);
    })).pipe(switchMap(() => {
      return this.triageService.triages(this.triageId);
    })).pipe(switchMap((triage) => {
      this.triage = triage;
      this.commitFetchStatus = "Fetching Git commit info";
      return this.getCommitsInBetween();
    })).pipe(switchMap(() => {
      return this.triageService.trials(this.triageId, null);
    })).pipe(switchMap((trials) => {
      this.trials = trials;
      if (this.trials && this.trials.length) {
        this.parseTrials(trials);
      }
      return of(true);
    })).subscribe(() => {

    }, error => {
      this.loggerService.error(error);
    });

  }

  parseTrials(trials) {
    trials.forEach((trial) => {
      if (this.commitMap.hasOwnProperty(trial.fun_os_sha)) {
        let commitNode = this.commitMap[trial.fun_os_sha];
        commitNode.status = trial.status;
        commitNode.tag = trial.tag;
        commitNode.jenkinsBuildNumber = trial.jenkins_build_number;
        commitNode.lsfJobId = trial.lsf_job_id;
        commitNode.trialSetId = trial.trial_set_id;
        commitNode.regexMatch = trial.regex_match;
        commitNode.selectedForTrial = true;
        commitNode.triageId = trial.triage_id;
        commitNode.trial = trial; // to store the whole trial object
        commitNode.result = trial.result;
        commitNode.reruns = trial.reruns;
        commitNode.id = trial.id;
        commitNode.originalId = trial.original_id;
        commitNode.active = trial.active;
        commitNode.submissionDateTime = trial.submission_date_time;
      }

    });

  }

  getCommitsInBetween() {
    return this.triageService.funOsCommits(this.triage.from_fun_os_sha, this.triage.to_fun_os_sha).pipe(switchMap((commits) => {

      commits.forEach((commit) => {
        let commitNode = new CommitNode();
        commitNode.date = commit.date;
        commitNode.funOsSha = commit.sha;
        commitNode.jenkinsBuildNumber = null;
        commitNode.lsfJobId = null;
        commitNode.status = -100; // TODO
        commitNode.selectedForTrial = false;
        commitNode.tag = null;
        commitNode.regexMatch = null;
        commitNode.triageId = null;
        commitNode.trial = null;
        this.commitMap[commitNode.funOsSha] = commitNode;
        this.commits.push(commitNode);
      });
      this.commitFetchStatus = null;
      return of(true);
    }));
  }

  showReruns(commit): void {
    if (this.currentRerunCommit) {
      this.hideReruns(this.currentRerunCommit);
    }
    new Observable(observer => {
      observer.next(true);
      return () => {
      }
    }).pipe(switchMap(() => {
      return this.triageService.trialReRuns(this.triageId, commit.id);
    })).pipe(switchMap((reRuns) => {
      this.reRuns = reRuns;
      commit.showReruns = true;
      this.currentRerunCommit = commit;
      return of(true);
    })).subscribe(() => {
    }, error => {
      this.loggerService.error(error);
    });

  }

  hideReruns(commit): void {
    commit.showReruns = false;
    this.reRuns = null;
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
      window.location.reload();
    }, error => {
      this.loggerService.error("Error starting the triage");
    })
  }

  restartTrial(commit) {
    let url = "/api/v1/triages/" + this.triageId + "/trials/" + commit.funOsSha;
    let payload = {"status": 20}; //TODO
    if (commit.hasOwnProperty("trial") && commit.trial) {
      let trial = commit.trial;
      payload["tag"] = trial.tag + "_" + trial.tags.length;
      let tempArray = Array.from(trial.tags);
      tempArray.push(trial.tag);
      payload["tags"] = tempArray;
    } else {
      payload["fun_os_sha"] = commit.funOsSha;
    }

    this.apiService.post(url, payload).subscribe((response) => {
      this.loggerService.success("Trial re-start submitted");
      setTimeout(() => {
        window.location.reload();
      }, 1000);

    })
  }

  getNumberOfSelections() {
    let numSelections = 0;
    this.commits.forEach((commit) => {
      if (commit.selected) {
        numSelections += 1;
      }
    });
    return numSelections;
  }

  clearSelections() {
    this.commits.forEach((commit) => {
      commit.selected = false;
    })
  }

  trySubset() {
    let numSelections = this.getNumberOfSelections();
    if (numSelections != 2) {
      return this.loggerService.error(`Please select two and only two commits`);
    }
    let commitsSelected = [];
    this.commits.forEach((commit) => {
      if (commit.selected) {
        commitsSelected.push(commit);
      }
    });

    let from_fun_os_sha = commitsSelected[1].funOsSha;
    let to_fun_os_sha = commitsSelected[0].funOsSha;
    let url = "/api/v1/triage_trial_set/" + this.triageId;
    let payload = {"from_fun_os_sha": from_fun_os_sha, "to_fun_os_sha": to_fun_os_sha};
    this.apiService.post(url, payload).subscribe((response) => {
      this.loggerService.success("New trial subset submitted");
      this.clearSelections();
      window.location.reload();
    }, error => {
      this.loggerService.error("Error submitting new trial subset");
    })
  }

  stopTriage() {
    this.triageService.stopTriage(this.triageId).subscribe((response) => {
      this.loggerService.success("Stop triage request sent");
      window.location.reload();
    }, error => {
      this.loggerService.error("Stop triage request failed");
    })
  }


}
