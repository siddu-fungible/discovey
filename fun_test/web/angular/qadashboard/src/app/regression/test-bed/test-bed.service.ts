import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class TestBedService {

  constructor(private apiService: ApiService) { }

  assets(name=null) {
    let url = "/api/v1/regression/assets";
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }));
  }

  unlockAsset(name, type) {
    let url = '/api/v1/regression/assets/' + name + "/" + type;
    let payload = {"manual_lock_user": null};
    return this.apiService.put(url, payload).pipe(switchMap(response => {
      return of(response.data);
    }))
  }

  lockAsset(name, type, submitter) {
    let url = "/api/v1/regression/assets/" + name + "/" + type;
    let payload = {"manual_lock_user": submitter};
    return this.apiService.put(url, payload).pipe(switchMap(response => {
      return of(response.data);
    }))
  }

}
