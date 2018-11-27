import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'jira-info',
  templateUrl: './jira-info.component.html',
  styleUrls: ['./jira-info.component.css']
})
export class JiraInfoComponent implements OnInit {

  @Input() url: any = null;
  jiraId: any;
  jiraIds: any;
  editingJira: boolean = false;
  showJiraInfo: boolean = false;

  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

  ngOnInit() {
    this.fetchJiraIds();
  }

  fetchJiraIds() :void {
     if (this.url) {
      this.apiService.get(this.url).subscribe((response) => {
        this.jiraIds = response.data;
      }, error => {
        this.loggerService.error("Fetching JiraIds failed");
      });
    }
  }

  submit(jiraId): void {
    this.apiService.get(this.url + '/' + jiraId).subscribe((response) => {
      alert("Submitted Successfully");
      this.editingJira = false;
      this.showJiraInfo = false;
      this.fetchJiraIds();
    }, error => {
      this.loggerService.error("Updating JiraIds failed");
    });
  }

  removeId(jiraId): void {
    this.apiService.get(this.url + '/delete/' + jiraId).subscribe((response) => {
      alert("Deleted Successfully");
      this.fetchJiraIds();
      }, error => {
        this.loggerService.error("Deleting JiraIds failed");
      });
  }

}
