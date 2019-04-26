import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";

@Component({
  selector: 'jira-info',
  templateUrl: './jira-info.component.html',
  styleUrls: ['./jira-info.component.css']
})
export class JiraInfoComponent implements OnInit {

  @Input() apiUrl: any = null;
  @Input() allowDelete = true;
  @Input() allowAdd = true;
  @Input() allowContext: boolean = false;
  @Input() summaryInHeader: boolean = true;
  @Input() showDetails: boolean = false;
  jiraId: string = null;
  jiraInfo: any = [];
  editingJira: boolean = false;
  showJiraInfo: boolean = false;
  @Output() numBugs: EventEmitter<number> = new EventEmitter();
  @Output() close: EventEmitter<boolean> = new EventEmitter();
  @Output() numActive: EventEmitter<number> = new EventEmitter();
  @Output() numResolved: EventEmitter<number> = new EventEmitter();

  status: string = null;
  activeBugs: number = 0;
  resolvedBugs: number = 0;
  sortOrderByColumnName: any = {};
  currentSortingColumn: string = "Severity";
  priorityList = ["Low", "Medium", "High", "Highest"];

  constructor(public apiService: ApiService, public loggerService: LoggerService, public commonService: CommonService) {
  }

  ngOnInit() {
    this.fetchJiraIds();
    this.sortOrderByColumnName["Severity"] = true;  // true == ascending
    this.sortOrderByColumnName["Priority"] = true;
    this.sortOrderByColumnName["Open since"] = true;

  }


  fetchJiraIds(): void {
    this.jiraInfo = [];
    if (this.apiUrl) {
      this.status = "Fetching";
      this.apiService.get(this.apiUrl).subscribe((response) => {
        this.jiraInfo = (Object.values(response.data));
        this.setActiveResolvedBugs();
        this.numBugs.emit(this.jiraInfo.length);
        this.jiraId = null;
        this.status = null;
        this.sortItems(this.jiraInfo);
      }, error => {
        this.loggerService.error("Fetching JiraIds failed");
        this.status = null;
      });
    }
  }

  sortItems(items) {
    items.sort((a, b) => {
      if (this.currentSortingColumn === 'Severity') {
        if (a.severity > b.severity) {
          return this.sortOrderByColumnName[this.currentSortingColumn] ? 1: -1;
        } else if (a.severity < b.severity) {
          return this.sortOrderByColumnName[this.currentSortingColumn] ? -1: 1;
        } else {
          return 0;
        }
      } else if (this.currentSortingColumn === 'Open since') {
        if (a.openSince > b.openSince) {
          return this.sortOrderByColumnName[this.currentSortingColumn] ? 1: -1;
        } else if (a.openSince < b.openSince) {
          return this.sortOrderByColumnName[this.currentSortingColumn] ? -1: 1;
        } else {
          return 0;
        }
      } else if (this.currentSortingColumn === 'Priority') {
        let aPriorityIndex = this.priorityList.indexOf(a.priority);
        let bPriorityIndex = this.priorityList.indexOf(b.priority);
        if (aPriorityIndex > bPriorityIndex) {
          return this.sortOrderByColumnName[this.currentSortingColumn] ? 1: -1;
        } else if (aPriorityIndex < bPriorityIndex) {
          return this.sortOrderByColumnName[this.currentSortingColumn] ? -1: 1;
        } else {
          return 0;
        }

      }
    })
  }


  setActiveResolvedBugs(): void {
    for (let info of this.jiraInfo) {
      if (info['status'] !== "Resolved" && info['status'] !== "Done" && info['status'] !== "Closed") {
        this.activeBugs += 1;
      } else {
        this.resolvedBugs += 1;
      }
      info["openSince"] = this.getDaysSince(info['created']);
    }
    this.numResolved.emit(this.resolvedBugs);
    this.numActive.emit(this.activeBugs);
  }

  closePanel(): void {
    this.close.emit(true);
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

  getDaysSince(d): number {
    let today = new Date();
    let oneDay = 24 * 60 * 60 * 1000;
    let localDate = this.commonService.convertToLocalTimezone(d);
    return Math.round(Math.abs((today.getTime() - localDate.getTime()) / (oneDay)));

  }

  setSortColumn(columnName) {
    this.sortOrderByColumnName[columnName] = !this.sortOrderByColumnName[columnName];
    this.currentSortingColumn = columnName;
    this.sortItems(this.jiraInfo);
  }
}
