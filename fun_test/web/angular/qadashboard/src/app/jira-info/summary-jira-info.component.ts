import {Component, EventEmitter, Input, Output} from '@angular/core';
import { JiraInfoComponent } from "./jira-info.component";

@Component({
  selector: 'summary-jira-info',
  templateUrl: './jira-info.component.html',
  styleUrls: ['./jira-info.component.css']
})
export class SummaryJiraInfoComponent extends JiraInfoComponent {
  @Input() bugApiUrl: any = null;
  @Input() data: any = new Set();
  @Input() allowContext: boolean = false;

fetchJiraIds(): void {
    this.jiraInfo = [];
    if (this.bugApiUrl) {
      this.status = "Fetching";
      let payload = {};
      payload["bug_ids"] = Object.keys(this.data);
      this.apiService.post(this.bugApiUrl, payload).subscribe((response) => {
        this.jiraInfo = (Object.values(response.data));
        this.setActiveResolvedBugs();
        this.status = null;
      }, error => {
        this.loggerService.error("Fetching BugIds failed");
        this.status = null;
      });
    }
  }
  getContextArray(id): any {
  let contextArray = this.data[id];
  let result = [];
  for (let context of contextArray) {
    context = context.substring(0, context.length - 2);
    if (context.indexOf("All metrics") === -1) {
      result.push(context);
    }
  }
  return result;
  }
}
