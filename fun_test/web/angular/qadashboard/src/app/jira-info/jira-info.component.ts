import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'jira-info',
  templateUrl: './jira-info.component.html',
  styleUrls: ['./jira-info.component.css']
})
export class JiraInfoComponent implements OnInit {

  @Input() url: any = null;
  jiraId: string = null;
  jiraInfo: any = [];
  editingJira: boolean = false;
  showJiraInfo: boolean = false;
  @Output() numBugs: EventEmitter<number> = new EventEmitter();
  status: string = null;

  constructor(private apiService: ApiService, private loggerService: LoggerService) {
  }

  ngOnInit() {
    this.fetchJiraIds();
  }

  fetchJiraIds(): void {
    this.jiraInfo = [];
    this.status = "Fetching";
    if (this.url) {
      this.apiService.get(this.url).subscribe((response) => {
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
      this.apiService.get(this.url + '/' + this.jiraId).subscribe((response) => {
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
    this.apiService.get(this.url + '/delete/' + id).subscribe((response) => {
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
