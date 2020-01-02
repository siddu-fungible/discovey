import { Injectable } from '@angular/core';
import {UserProfile} from "./definitions";
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {ApiService} from "../services/api/api.service";

@Injectable({
  providedIn: 'root'
})
export class AuthenticationService {
  userProfile: UserProfile;
  constructor(private apiService: ApiService) { }

  getUserProfile() {
    let userProfile = new UserProfile();
    return userProfile.get(userProfile.getUrl()).pipe(switchMap(response => {
      this.userProfile = userProfile;
      return of(userProfile);
    }))
  }

  login(email) {
    let payload = {email: email};
    return this.apiService.post('/api/v1/login', payload).pipe(switchMap(response => {
      return of(response.data);
    }))
  }

}
