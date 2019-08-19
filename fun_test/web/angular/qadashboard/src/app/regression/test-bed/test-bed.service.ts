import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {error} from "util";
import {LoggerService} from "../../services/logger/logger.service";

@Injectable({
  providedIn: 'root'
})
export class TestBedService {

  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

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

  testBeds() {
    let url = "/api/v1/regression/test_beds";
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }), catchError((error) => {
      this.loggerService.error("Unable to fetch test-beds");
      return of(null);
    }))
  }

  assetTypes() {
    let url = "/api/v1/regression/asset_types";
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }), catchError(error => {
      throw(error);
    }))
  }

}
