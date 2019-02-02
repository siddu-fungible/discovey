import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {CommonService} from "../services/common/common.service";

@Component({
  selector: 'git-history',
  templateUrl: './triage.component.html',
  styleUrls: ['./triage.component.css']
})
export class TriageComponent implements OnInit {
  @Input() id: number = null;
  // @Input() faultyCommit: string = null;
  // @Input() successCommit: string = '0af7f75c8a6f89620792ecd6f46212cda81a40b3';
  faultyCommit: string = null;
  successCommit: string = null;
  commits: any = null;
  changedFiles: any = null;
  commitDates: any = null;
  status: string = null;
  showChanged: boolean = false;
  gitCommit: any = null;
  faultyMessage: string = null;
  successMessage: string = null;
  totalShow: boolean = false;
  gitUser: string = null;
  triageInfo: any = null;

  constructor(private apiService: ApiService, private logger: LoggerService, private route: ActivatedRoute, private commonService: CommonService) { }

  ngOnInit() {
    this.status = "Fetching Commits";
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.id = params['id'];
        this.setCommits();
      }
      else if (this.id) {
        this.setCommits();
      }
    });

  }

  setCommits(): void {
    let payload = {"metric_id": this.id};
    this.apiService.post('/metrics/first_degrade', payload).subscribe((data) => {
      let result = data.data;
      this.triageInfo = result;
      if (result.passed_git_commit && result.passed_git_commit !== "") {
        this.successCommit = result.passed_git_commit;
      }
      if (result.degraded_git_commit && result.degraded_git_commit !== "") {
        this.faultyCommit = result.degraded_git_commit;
      }
      this.fetchGitCommits();
    }, error => {
      this.logger.error("Past Status Urls");
    });

  }

  fetchGitCommits(): void {
    if (this.faultyCommit && this.successCommit) {
      let payload = {};
      payload = {"faulty_commit": this.faultyCommit,
                 "success_commit": this.successCommit};
      this.apiService.post('/metrics/git_commits', payload).subscribe(result => {
        this.commits = result.data.commits;
        let total = this.commits.length - 1;
        this.faultyMessage = this.commits[0].message;
        this.successMessage = this.commits[total].message;
        this.status = null;
        let payload = {"metric_id": this.id,
        "commits": this.commits,
        "triage_info": this.triageInfo};
        this.apiService.post('/metrics/triage_db', payload).subscribe(response => {
          alert("submitted");
        }, error => {
          this.logger.error("Updating DB Failed");
        });
      }, error => {
        this.logger.error("Fetching git Commits between the faulty and success commits");
      });
    }
    else{
      this.status = null;
      console.log("Git commit is missing from the data");
    }
  }

  showFilesChanged(commit): void {
    this.showChanged = true;
    this.totalShow = false;
    this.commonService.scrollTo("changed-files");
    this.changedFiles = commit.changed_files;
    this.gitCommit = commit.hexsha;
    this.gitUser = commit.author;

  }

  showTotalFilesCHanged(): void {
    this.showChanged = true;
    this.totalShow = true;
    this.commonService.scrollTo("changed-files");
    let changedFiles = new Set();
    for (let commit of this.commits) {
      for (let file of commit.changed_files) {
        changedFiles.add(file);
      }
    }
    this.changedFiles = changedFiles;
  }
}
