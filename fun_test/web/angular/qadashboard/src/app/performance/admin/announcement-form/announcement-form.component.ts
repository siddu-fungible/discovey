import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2, ViewChild} from '@angular/core';
import {ApiService} from "../../../services/api/api.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {CommonService} from "../../../services/common/common.service";
import {RegressionService} from "../../../regression/regression.service";
import {Announcement} from "./announcement";


@Component({
  selector: 'app-announcement-form',
  templateUrl: './announcement-form.component.html',
  styleUrls: ['./announcement-form.component.css']
})


export class AnnouncementFormComponent implements OnInit {
  @ViewChild('announcementForm') formValues;
  editing: boolean = false;
  levels = {'1': 'info', '2': 'warning', '3': 'danger'};
  level_nums = Object.keys(this.levels);
  announcementModel = new Announcement('', null);
  tempAnnouncementModel = new Announcement('', null);
  emptyAnnouncement = new Announcement('', 1);
  fetched: boolean = false;
  currentLevel: number;

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
      this.currentLevel = this.levels[this.announcementModel.level];
      this.fetched = true;
    }, error => {
      this.logger.error("Unable to fetch announcements");
    })

  }

}


