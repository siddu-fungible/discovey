import { Component, OnInit } from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";

@Component({
  selector: 'app-announcement',
  templateUrl: './announcement.component.html',
  styleUrls: ['./announcement.component.css']
})
export class AnnouncementComponent implements OnInit {
  show: boolean = false;
  constructor(private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService) { }
  message: string = null;
  level: number = 1;
  ngOnInit() {
    this.checkForAnnouncements();
    setInterval(() => {
      this.checkForAnnouncements();
    }, 60 * 1000);
  }

  checkForAnnouncements() {
    this.apiService.get('/api/v1/site_configs').subscribe((response) => {
      if (response.data) {
        this.message = response.data.announcement;
        if (this.message.length > 0) {
          this.commonService.setAnnouncement();
        } else {
          this.commonService.clearAnnouncement();
        }
        this.level = response.data.announcement_level;
      }
      this.show = this.message.length > 0;
    }, error => {
      this.loggerService.error("Unable to fetch announcements");
    });
  }

}
