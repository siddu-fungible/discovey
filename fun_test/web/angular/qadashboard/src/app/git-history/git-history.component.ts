import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'git-history',
  templateUrl: './git-history.component.html',
  styleUrls: ['./git-history.component.css']
})
export class GitHistoryComponent implements OnInit {
  @Input() faultyCommit: string = null;
  @Input() successCommit: string = '0af7f75c8a6f89620792ecd6f46212cda81a40b3';
  commits: any = null;
  changedFiles: any = null;
  status: string = null;

  constructor(private apiService: ApiService, private logger: LoggerService) { }

  ngOnInit() {
    this.status = "Fetching Commits";
    this.fetchGitCommits();
  }

  fetchGitCommits(): void{
    if (this.faultyCommit && this.successCommit) {
      let payload = {};
      payload = {"faulty_commit": this.faultyCommit,
                 "success_commit": this.successCommit};
      this.apiService.post('/metrics/git_commits', payload).subscribe(result => {
        this.commits = result.data.commits;
        this.changedFiles = result.data.changed_files;
        this.status = null;
      }, error => {
        this.logger.error("Fetching git Commits between the faulty and success commits");
      });
    }
    else{
      this.status = null;
    }
  }
}
