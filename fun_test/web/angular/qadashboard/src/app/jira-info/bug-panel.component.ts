import {Component, Input} from '@angular/core';
import { JiraInfoComponent } from "./jira-info.component";

@Component({
  selector: 'bug-panel',
  templateUrl: './jira-info.component.html',
  styleUrls: ['./jira-info.component.css']
})
export class BugPanelComponent extends JiraInfoComponent {
  @Input() bugApiUrl: any = null;
  @Input() data: any = new Set();
fetchJiraIds(): void {
    this.jiraInfo = [];
    if (this.bugApiUrl) {
      this.status = "Fetching";
      let payload = {};
      payload["bug_ids"] = this.data;
      this.apiService.post(this.bugApiUrl, payload).subscribe((response) => {
        this.jiraInfo = (Object.values(response.data));
        this.status = null;
      }, error => {
        this.loggerService.error("Fetching BugIds failed");
        this.status = null;
      });
    }
  }
}
