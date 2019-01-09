import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'git-history',
  templateUrl: './git-history.component.html',
  styleUrls: ['./git-history.component.css']
})
export class GitHistoryComponent implements OnInit {
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

  constructor(private apiService: ApiService, private logger: LoggerService, private route: ActivatedRoute) { }

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
    this.apiService.post('/metrics/chart_info', payload).subscribe((data) => {
      let result = data.data;
      if (result.last_git_commit && result.last_git_commit !== "") {
        this.faultyCommit = result.last_git_commit;
        this.fetchGitCommits();
      }
    }, error => {
      this.logger.error("Current Failed Urls");
    });

    let payload1 = {"metric_id": this.id};
    this.apiService.post('/metrics/past_status', payload1).subscribe((data) => {
      let result = data.data;
      if (result.passed_git_commit && result.passed_git_commit !== "") {
        this.successCommit = result.passed_git_commit;
        this.fetchGitCommits();
      }
    }, error => {
      this.logger.error("Past Status Urls");
    });

  }

  fetchGitCommits(): void{
    if (this.faultyCommit && this.successCommit) {
      let payload = {};
      payload = {"faulty_commit": this.faultyCommit,
                 "success_commit": this.successCommit};
      this.apiService.post('/metrics/git_commits', payload).subscribe(result => {
        this.commits = result.data.commits;
        this.status = null;
      }, error => {
        this.logger.error("Fetching git Commits between the faulty and success commits");
      });
    }
    // else{
    //   this.status = null;
    // }
  }

  showFilesChanged(): void {

  }
}
