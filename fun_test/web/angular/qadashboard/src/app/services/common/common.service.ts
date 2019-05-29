import { Injectable } from '@angular/core';
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class CommonService {
  newAlert: boolean = false;
  constructor() {

  }

  scrollTo(elementId) {
    let element = document.getElementById(elementId);
    window.scrollTo({left: 0, top: element.offsetTop, behavior: "smooth"});
  }

  timestampToDate(timestampInMs) {
    return new Date(timestampInMs);
  }

  clearAlert() {
    this.newAlert = false;
  }

  setAlert() {
    this.newAlert = true;
  }

  monitorAlerts() {
    return new Observable(observer => {
      //observer.next(this.newAlert);
      setInterval(() => observer.next(this.newAlert), 1000);
      return () => {};
    })
  }

  convertToLocalTimezone(t): Date {
    let d = new Date(t.replace(/\s+/g, 'T'));
    let epochValue = d.getTime();
    return new Date(epochValue);
  }

  getPrettyLocalizeTime(t) {
    let result = t;
    try {
      result = this.convertToLocalTimezone(t).toLocaleString().replace(/\..*$/, "");
    } catch (e) {
      console.log(e);
    }
    return result;
  }
}
