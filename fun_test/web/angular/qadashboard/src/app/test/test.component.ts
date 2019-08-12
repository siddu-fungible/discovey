import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {from, Observable, of} from "rxjs";
import {mergeMap, switchMap} from "rxjs/operators";
import {CommonService} from "../services/common/common.service";
import {RegressionService} from "../regression/regression.service";
import {Announcement} from "./announcement";
import {FormGroup} from "@angular/forms";

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})

export class TestComponent implements OnInit {
  @ViewChild('announcementForm') formValues;
  editing: boolean = false;
  showMsg: boolean = false;
  levels = {'1': 'info', '2': 'warning', '3': 'danger'};
  level_nums = Object.keys(this.levels);
  announcementModel = new Announcement('', null);
  tempAnnouncementModel = new Announcement('', null);
  emptyAnnouncement = new Announcement('', null);
  fetched: boolean = false;
  mylevel: string = '2';

  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService, private regressionService: RegressionService) {
  }


  ngOnInit() {
    this.refresh();

  }

  onSubmit() {
    this.apiService.put('/api/v1/site_configs', this.tempAnnouncementModel).subscribe((response) => {
      this.logger.success('Successfully submitted!');
      this.refresh();
    }, error => {
      this.logger.error("Unable to submit announcements");
    });
    this.editing = false;
  }

  onCancel() {
    this.editing = false;
    this.tempAnnouncementModel.message = this.announcementModel.message;
    this.tempAnnouncementModel.level = this.announcementModel.level;
  }

  onDeleteAnnouncement() {
    if (confirm('Are you sure you want to delete current announcement?')) {
      this.apiService.put('/api/v1/site_configs', this.emptyAnnouncement).subscribe(response => {
        this.logger.success('Successfully deleted!');
        //window.location.reload();
      }, error => {
        this.logger.error("Deletion failed");
      });
    }
  }

  test() {
    console.log(this.tempAnnouncementModel);
  }


  refresh() {
    this.apiService.get('/api/v1/site_configs').subscribe((response) => {
      this.announcementModel.message = response.data.announcement;
      this.announcementModel.level = response.data.announcement_level;
      this.tempAnnouncementModel.message = this.announcementModel.message;
      this.tempAnnouncementModel.level = this.announcementModel.level;
      this.tempAnnouncementModel = {...this.tempAnnouncementModel};
      this.fetched = true;
    }, error => {
      this.logger.error("Unable to fetch announcements");
    })

  }


}


