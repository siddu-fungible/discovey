import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {LoggerService} from "../../services/logger/logger.service";

@Injectable({
  providedIn: 'root'
})
export class TestBedService {

  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

  assets(name=null) {
    let url = "/api/v1/regression/assets";
    if (name) {
      url += `?test_bed_name=${name}`;
    }
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

  lockAsset(name, type, submitter, minutes=1) {
    let url = "/api/v1/regression/assets/" + name + "/" + type;
    let payload = {manual_lock_user: submitter, minutes: minutes};
    return this.apiService.put(url, payload).pipe(switchMap(response => {
      return of(response.data);
    }))
  }

  enableAsset(name, type, disabled) {
    let url = "/api/v1/regression/assets/" + name + "/" + type;
    let payload = {disabled: disabled};
    return this.apiService.put(url, payload).pipe(switchMap(response => {
      return of(response.data);
    }))
  }

  healthCheckEnabledAsset(name, type, enabled) {
    let url = "/api/v1/regression/assets/" + name + "/" + type;
    let payload = {health_check_enabled: enabled};
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

  poolMemberTypeOptionToString(assetType, typeCode) {
    let result = "";
    if (assetType === 'DUT') {
      result = ["Default", "With servers", "With SSDs"][parseInt(typeCode)]; //TODO this should be a service
    }
    return result;
  }

}
