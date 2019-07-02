import { Injectable } from '@angular/core';
import {ApiService} from 'src/app/services/api/api.service';
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {LoggerService} from "../logger/logger.service";

@Injectable({
  providedIn: 'root'
})
export class UserService {
  allUsers: any = null;
  userMap: {[email: string]: any} = null;
  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

  users() {
    let url = "/api/v1/users";
    return this.apiService.get(url).pipe(switchMap((response)=> {
      return of(response.data);
    }))
  }

  getUserMap() {

    if (!this.userMap) {
      return this.users().pipe(switchMap(((response) => {
        this.allUsers = response;
        this.userMap = {};
        this.allUsers.map((user) => {
          this.userMap[user.email] = user;
        });
        return of(this.userMap)
      })))

    } else {
      return of(this.userMap);
    }

  }
}
