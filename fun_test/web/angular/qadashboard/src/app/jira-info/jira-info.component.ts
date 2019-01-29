import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'jira-info',
  templateUrl: './jira-info.component.html',
  styleUrls: ['./jira-info.component.css']
})
export class JiraInfoComponent implements OnInit {

  @Input() apiUrl: any = null;
  @Input() allowDelete = true;
  @Input() allowAdd = true;
  jiraId: string = null;
  jiraInfo: any = [];
  editingJira: boolean = false;
  showJiraInfo: boolean = false;
  @Output() numBugs: EventEmitter<number> = new EventEmitter();
  status: string = null;

  constructor(public apiService: ApiService, public loggerService: LoggerService) {
  }

  ngOnInit() {
    this.fetchJiraIds();
  }

  fetchJiraIds(): void {
    this.jiraInfo = [];
    if (this.apiUrl) {
      this.status = "Fetching";
      this.apiService.get(this.apiUrl).subscribe((response) => {
        this.jiraInfo = (Object.values(response.data));
        this.numBugs.emit(this.jiraInfo.length);
        this.jiraId = null;
        this.status = null;
      }, error => {
        this.loggerService.error("Fetching JiraIds failed");
        this.status = null;
      });
    }
  }

  submit(): void {
    if (this.jiraId === null) {
      alert("Enter some ID");
    } else {
      let payload = {jira_id: this.jiraId};
      this.apiService.post(this.apiUrl, payload).subscribe((response) => {
        alert("Submitted Successfully");
        this.editingJira = false;
        this.showJiraInfo = false;
        this.fetchJiraIds();
      }, error => {
        this.loggerService.error("Updating JiraIds failed");
        alert("Validation Failed. Invalid Bug Id");
      });
    }
  }

  removeId(id): void {
    this.apiService.delete(this.apiUrl + "/" + id).subscribe((response) => {
      alert("Deleted Successfully");
      this.fetchJiraIds();
    }, error => {
      this.loggerService.error("Deleting JiraIds failed");
    });
  }

  openUrl(url): void {
    window.open(url, '_blank');
  }

}
