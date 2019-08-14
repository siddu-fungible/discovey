import {Component, OnInit, ViewChild} from '@angular/core';
import {ApiService} from "../../../services/api/api.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {Announcement} from "../../../announcement/announcement";


@Component({
  selector: 'app-announcement-form',
  templateUrl: './announcement-form.component.html',
  styleUrls: ['./announcement-form.component.css']
})


export class AnnouncementFormComponent implements OnInit {
  @ViewChild('announcementForm') formValues;
  editing: boolean = false;
  levels = {1: 'info', 2: 'warning', 3: 'danger'};
  levelNums = [1, 2, 3];
  announcementModel = new Announcement('', null);
  tempAnnouncementModel = new Announcement('', null);
  emptyAnnouncement = new Announcement('', 1);
  fetched: boolean = false;
  currentLevel: number;

  constructor(private apiService: ApiService, private logger: LoggerService) {
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
    this.tempAnnouncementModel.announcement = this.announcementModel.announcement;
    this.tempAnnouncementModel.announcementLevel = this.announcementModel.announcementLevel;
  }

  onDeleteAnnouncement() {
    if (confirm('Are you sure you want to delete current announcement?')) {
      this.apiService.put('/api/v1/site_configs', this.emptyAnnouncement).subscribe(response => {
        this.logger.success('Successfully deleted!');
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
      this.announcementModel.announcement = response.data.announcement;
      this.announcementModel.announcementLevel = response.data.announcement_level;
      this.tempAnnouncementModel.announcement = this.announcementModel.announcement;
      this.tempAnnouncementModel.announcementLevel = this.announcementModel.announcementLevel;
      this.tempAnnouncementModel = {...this.tempAnnouncementModel};
      this.currentLevel = this.levels[this.announcementModel.announcementLevel];
      this.fetched = true;
    }, error => {
      this.logger.error("Unable to fetch announcements");
    })

  }

}


