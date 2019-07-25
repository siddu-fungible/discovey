import {Component, OnInit} from '@angular/core';
import {CommonService} from "./services/common/common.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  showAlert: boolean = false;
  hasAnnouncement: boolean = true;
  title = 'qadashboard';
  constructor(private commonService: CommonService) {}
  ngOnInit() {
    this.commonService.monitorAlerts().subscribe((newAlertValue: boolean) => {
      this.showAlert = newAlertValue;
    });

    this.commonService.monitorAnnouncements().subscribe((announcementAvailable: boolean) => {
      this.hasAnnouncement = announcementAvailable;
    })
  }
}
