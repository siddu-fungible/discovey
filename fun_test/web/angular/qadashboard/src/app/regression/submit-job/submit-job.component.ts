import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";

@Component({
  selector: 'app-submit-job',
  templateUrl: './submit-job.component.html',
  styleUrls: ['./submit-job.component.css']
})
export class SubmitJobComponent implements OnInit {
  scheduleInMinutes: number;
  scheduleInMinutesRadio: boolean;
  buildUrl: string;
  selectedSuite: any;
  selectedInfo: any;
  jobId: number;
  suitesInfo: any;
  selectedTags: any;
  tags: any;
  emailOnFailOnly: boolean;
  schedulingOptions: any;
  scheduleInMinutesRepeat: any;
  scheduleAt: any;
  scheduleAtRepeat: any;
  emails: any;


  constructor(private apiService: ApiService, private logger: LoggerService) {
  }

  ngOnInit() {
    this.scheduleInMinutes = 1;
    this.scheduleInMinutesRadio = true;
    this.buildUrl = "http://dochub.fungible.local/doc/jenkins/funsdk/latest/";
    this.selectedSuite = null;
    this.selectedInfo = null;
    this.jobId = null;
    let self = this;
    this.apiService.get("/regression/suites").subscribe(function (result) {
      self.suitesInfo = result.data;
    });
    this.selectedTags = [];
    this.tags = [];
    this.fetchTags();
    this.emailOnFailOnly = false;
  }

  fetchTags(): void {
    let self = this;
    this.apiService.get('/regression/tags').subscribe(function (result) {
      let data = result.data;
      data.forEach(function (item) {
        self.tags.push({name: item.fields.tag});
      });

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
      tags.push(item.name);
    });
    return tags;
  }

  testClick() {
    this._getSelectedtags().forEach(function (item) {
      console.log(item);
    });

  }

  submitClick(formIsValid) {
    let self = this;
    if (!formIsValid) {
      this.logger.error("Form is invalid");
      return;
    }
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
