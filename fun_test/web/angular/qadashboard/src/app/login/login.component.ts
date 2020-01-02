import {Component, EventEmitter, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {UserProfile} from "./definitions";
import {AuthenticationService} from "./authentication.service";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Output} from '@angular/core';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  email: string = null;
  next: string = null;
  @Output() loginSuccessful = new EventEmitter<boolean>();
  constructor(private apiService: ApiService,
              private authenticationService: AuthenticationService,
              private loggerService: LoggerService,
              private commonService: CommonService,
              private router: Router) { }

  ngOnInit() {

    this.commonService.getRouterQueryParam().subscribe(queryParameters => {
      if (queryParameters.hasOwnProperty('next')) {
        this.next = queryParameters.next;
      }
    })

    /*
    */
    /*this.apiService.get('/api/v1/login').subscribe(response => {
      if (!response.data) {
        let payload = {username: "john", password: "fun123fun123"};
        this.apiService.post('/api/v1/login', payload).subscribe(response => {
        let userProfile = new UserProfile();
        userProfile.get(userProfile.getUrl(null)).subscribe(response => {
          let i = response;
        })
        })
      } else {
        this.username = response.data;
        let userProfile = new UserProfile();
        userProfile.get(userProfile.getUrl(null)).subscribe(response => {
          let i = response;
        })
      }
    })*/
  }

  login(email) {
    this.authenticationService.login(this.email).subscribe(response => {
      this.loginSuccessful.emit(true);
    }, error => {
      this.loggerService.error(`Unable to login ${email}`, error);
    })
  }

  logout() {
    this.apiService.post('/api/v1/logout', null).subscribe(response => {
    })
  }
}
