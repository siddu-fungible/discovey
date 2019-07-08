import { Component, OnInit } from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'app-announcement',
  templateUrl: './announcement.component.html',
  styleUrls: ['./announcement.component.css']
})
export class AnnouncementComponent implements OnInit {
  show: boolean = false;
  constructor(private apiService: ApiService, private loggerService: LoggerService) { }
  message: string = null;
  ngOnInit() {
    this.checkForAnnouncements();
  }

  checkForAnnouncements() {
    this.apiService.get('/api/v1/site_configs').subscribe((response) => {
      if (response.data) {
        this.message = response.data.announcement;
      }

      this.show = this.message.length > 0;

    }, error => {
      this.loggerService.error("Unable to fetch announcements");
    });
  }

}
