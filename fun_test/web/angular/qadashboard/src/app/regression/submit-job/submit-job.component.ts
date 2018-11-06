import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {Title} from "@angular/platform-browser";

@Component({
  selector: 'app-submit-job',
  templateUrl: './submit-job.component.html',
  styleUrls: ['./submit-job.component.css']
})
export class SubmitJobComponent implements OnInit {
  scheduleInMinutes: number;
  scheduleInMinutesRadio: boolean;
  buildUrl: string;
  selectedSuite: string = null;
  selectedInfo: any;
  jobId: number;
  suitesInfo: any;
  selectedTags: any[] = [];
  tags: any;
  emailOnFailOnly: boolean;
  schedulingOptions: boolean;
  scheduleInMinutesRepeat: any;
  scheduleAt: any;
  scheduleAtRepeat: any;
  emails: any;
  suitesInfoKeys: any = [];
  selectTags: any[] = [];
  dropdownSettings = {};


  constructor(private apiService: ApiService, private logger: LoggerService,
              private title: Title) {
  }

  ngOnInit() {
    this.title.setTitle('Submit Jobs');
    this.dropdownSettings = {
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      itemsShowLimit: 3,
      allowSearchFilter: true
    };
    this.scheduleInMinutes = 1;
    this.scheduleAtRepeat = false;
    this.scheduleInMinutesRepeat = null;
    this.selectTags = [];
    this.scheduleAt = null;
    this.scheduleInMinutesRadio = true;
    this.buildUrl = "http://dochub.fungible.local/doc/jenkins/funsdk/latest/";
    this.selectedSuite = null;
    this.selectedInfo = null;
    this.schedulingOptions = false;
    this.jobId = null;
    let self = this;
    this.apiService.get("/regression/suites").subscribe((result) => {
      let suitesInfo = JSON.parse(result.data);
      self.suitesInfo = suitesInfo;
      for (let suites of Object.keys(suitesInfo)) {
        self.suitesInfoKeys.push(suites);
      }
    });
    this.selectedTags = [];
    this.tags = [];
    this.fetchTags();
    this.emailOnFailOnly = false;
  }

  onItemSelect (item:any): void {
    console.log(item);
  }
  onSelectAll (items: any): void {
    console.log(items);
  }

  fetchTags(): void {
    let self = this;
    this.apiService.get('/regression/tags').subscribe(function (result) {
      let data = JSON.parse(result.data);
      let i = 1;
      self.selectTags = [];
      for (let item of data) {
        self.tags.push({name: item.fields.tag});
        self.selectTags.push({item_id: i++, item_text: item.fields.tag});
      }
      //self.selectedTags = self.tags
    }, error => {
      this.logger.error("unable to fetch tags");
    });
  }

  changedValue(selectedSuite) {
    this.selectedInfo = this.suitesInfo[selectedSuite];
  }

  getSchedulingOptions(payload) {
    if (this.schedulingOptions) {
      if (this.scheduleInMinutesRadio) {
        if (!this.scheduleInMinutes) {
          this.logger.error("Please enter the schedule in minutes value");
        } else {
          payload["schedule_in_minutes"] = this.scheduleInMinutes;
          payload["schedule_in_minutes_repeat"] = this.scheduleInMinutesRepeat;
        }

      } else {
        if (!this.scheduleAt) {
          this.logger.error("Please enter the schedule at value");
          return;
        } else {
          payload["schedule_at"] = this.scheduleAt;
          payload["schedule_at_repeat"] = this.scheduleAtRepeat;
        }

      }
    }
    return payload;
  }

  _getSelectedtags() {
    let tags = [];
    this.selectedTags.forEach(function (item) {
      tags.push(item.item_text);
    });
    return tags;
  }

  submitClick() {
    let self = this;
    this.jobId = null;
    let payload = {};
    payload["suite_path"] = this.selectedSuite;
    payload["build_url"] = this.buildUrl;
    payload["tags"] = this._getSelectedtags();
    payload["email_on_fail_only"] = this.emailOnFailOnly;
    if (this.emails) {
      this.emails = this.emails.split(",");
      payload["email_list"] = this.emails
    }

    if (this.schedulingOptions) {
      payload = this.getSchedulingOptions(payload);
    }
    this.apiService.post('/regression/submit_job', payload).subscribe(function (result) {
      self.jobId = parseInt(result.data);
      window.location.href = "/regression/suite_detail/" + self.jobId;
      console.log("Job " + self.jobId + " Submitted");
    }, error => {
      self.logger.error("Unable to submit job");
    });
  }

}
