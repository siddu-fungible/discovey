import { Component, OnInit } from '@angular/core';
import {ApiService} from "../services/api/api.service";

@Component({
  selector: 'app-scheduler-admin',
  templateUrl: './scheduler-admin.component.html',
  styleUrls: ['./scheduler-admin.component.css']
})
export class SchedulerAdminComponent implements OnInit {
  gitLogs = null;
  gitPullLog = null;
  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.fetchGitLogs();
  }

  gitPull() {
    let payload = {command: "pull"};
    this.apiService.post('/regression/git', payload).subscribe(response => {
        this.gitPullLog = response.data.pull;
        this.fetchGitLogs();

      }
    )
  }
  fetchGitLogs() {
    let payload = {command: "logs"};
    this.apiService.post('/regression/git', payload).subscribe(response => {
        this.gitLogs = response.data.logs;

      }
    )
  }
}
