import {Component, OnInit} from '@angular/core';
import {CommonService} from "./services/common/common.service";
import {AuthenticationService} from "./login/authentication.service";
import {UserProfile} from "./login/definitions";
import {Router} from "@angular/router";
import {LoggerService} from "./services/logger/logger.service";
import {ApiService} from "./services/api/api.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  showAlert: boolean = false;
  userProfile: UserProfile = null;
  hasAnnouncement: boolean = true;
  title = 'qadashboard';
  userProfileReady: boolean = false;
  doLogin: boolean = false;
  email: string = null;
  constructor(private commonService: CommonService,
              private authenticationService: AuthenticationService,
              private router: Router,
              private loggerService: LoggerService,
              private apiService: ApiService) {}

  ngOnInit() {

    this.fetchUserProfile();

    this.commonService.monitorAlerts().subscribe((newAlertValue: boolean) => {
      this.showAlert = newAlertValue;
    });

    this.commonService.monitorAnnouncements().subscribe((announcementAvailable: boolean) => {
      this.hasAnnouncement = announcementAvailable;
    })
  }

  fetchUserProfile() {
    this.authenticationService.getUserProfile().subscribe(response => {
      let userProfile: UserProfile = response;
      if (userProfile.is_anonymous || !userProfile.user || !userProfile.user.is_authenticated) {
        this.doLogin = true;
      } else {
        this.userProfileReady = true;
        this.commonService.setUserProfile(userProfile);
        this.userProfile = userProfile;
      }
    });
  }

  loginSuccessful(loginResult) {
    if (loginResult) {
      this.doLogin = false;
      this.fetchUserProfile();
    }
  }

  login() {
    this.authenticationService.login(this.email).subscribe(response => {
      this.loginSuccessful(true);
    }, error => {
      this.loggerService.error(`Unable to login ${this.email}`, error);
    })
  }


  logout() {
    this.apiService.post('/api/v1/logout', null).subscribe(response => {
      window.location.reload();
    })
  }
}
