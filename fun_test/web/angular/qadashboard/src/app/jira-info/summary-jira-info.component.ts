import {Component, EventEmitter, Input, Output} from '@angular/core';
import {JiraInfoComponent} from "./jira-info.component";

@Component({
  selector: 'summary-jira-info',
  templateUrl: './jira-info.component.html',
  styleUrls: ['./jira-info.component.css']
})
export class SummaryJiraInfoComponent extends JiraInfoComponent {
  @Input() bugInfoUrl: any = null;
  @Input() data: any = new Set();

  fetchJiraIds(): void {
    this.jiraInfo = [];
    if (this.bugInfoUrl) {
      this.status = "Fetching";
      let payload = {};
      payload["bug_ids"] = Object.keys(this.data);
      this.apiService.post(this.bugInfoUrl, payload).subscribe((response) => {
        this.jiraInfo = (Object.values(response.data));
        this.setActiveResolvedBugs();
        this.status = null;
      }, error => {
        this.loggerService.error("Fetching BugIds failed");
        this.status = null;
      });
    }
  }

}
