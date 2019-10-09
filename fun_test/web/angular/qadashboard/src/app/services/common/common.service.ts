import {Injectable} from '@angular/core';
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class CommonService {
  newAlert: boolean = false;
  announcementAvailable: boolean = false;

  constructor() {

  }

  scrollTo(elementId) {
    let element = document.getElementById(elementId);
    //window.scrollTo({left: 0, top: 80, behavior: "smooth"});
    element.scrollIntoView({behavior: "smooth", block: "center", inline: "nearest"});

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
      return () => {
      };
    })
  }

  convertToLocalTimezone(t): Date {
    let d = new Date(t.replace(/\s+/g, 'T'));
    let epochValue = d.getTime();
    return new Date(epochValue);
  }

  convertToTimezone(dateTime, timeZone) {
    if (dateTime instanceof Date) {
      dateTime = dateTime;
    } else {
      let d = new Date(dateTime.replace(/\s+/g, 'T'));
      let epochValue = d.getTime();
      dateTime = new Date(epochValue);
    }
    let pstDate = new Date(dateTime.toLocaleString('en-US', {
      timeZone: timeZone
    }));
    return pstDate;
  }

  convertEpochToDate(epoch, timeZone=null): Date {
    let dateTime = new Date(epoch);
    if (timeZone) {
      dateTime = this.convertToTimezone(dateTime, timeZone);
    }
    return dateTime;
  }

  convertDateToEpoch(dateTimeObj): Date {
    let epochValue = dateTimeObj.getTime();
    return epochValue;
  }

  isSameDay(d1, d2) {
    return d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate();
  }

  setAnnouncement() {
    this.announcementAvailable = true;
  }

  clearAnnouncement() {
    this.announcementAvailable = false;
  }

  monitorAnnouncements() {
    return new Observable(observer => {
      setInterval(() => observer.next(this.announcementAvailable), 1000);
      return () => {
      };
    })
  }

  getPrettyPstTime(t) {
    let result = t;
    try {
      result = this.convertToTimezone(t, "America/Los_Angeles").toLocaleString().replace(/\..*$/, "");
    } catch (e) {
      console.log(e);
    }
    return result;
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

  getShortDate(t) {
    let result = t;
    try {
      result = t.toLocaleString().replace(/\..*$/, "");
    } catch (e) {
      console.log(e);
    }
    return result;
  }

  addLeadingZeroesToDate(localDate): string {
    let localDateString = (localDate.getDate() < 10 ? '0' : '') + localDate.getDate();
    let localMonthString = ((localDate.getMonth() + 1) < 10 ? '0' : '') + (localDate.getMonth() + 1);
    let localYearString = String(localDate.getFullYear());
    // let keySplitString = localDate.toLocaleString("default", {hourCycle: "h24"}).split(" ");
    // let timeString = keySplitString[1].split(":");
    let localHour = (localDate.getHours());
    let localMinutes = (localDate.getMinutes());
    let localSeconds = (localDate.getSeconds());
    let hour = ((Number(localHour) < 10) ? '0' : '') + localHour + ":";
    let minutes = ((Number(localMinutes) < 10) ? '0' : '') + localMinutes + ":";
    let seconds = ((Number(localSeconds) < 10) ? '0' : '') + localSeconds;
    let keyString = localMonthString + "/" + localDateString + "/" + localYearString + ", " + hour + minutes + seconds;
    return keyString;
  }

  getEpochBounds(dateTime): number[] {
    dateTime.setHours(23);
    dateTime.setMinutes(59);
    dateTime.setSeconds(59);
    dateTime.setMilliseconds(0);
    let toEpoch = dateTime.getTime();
    dateTime.setHours(0);
    dateTime.setMinutes(0);
    dateTime.setSeconds(1);
    dateTime.setMilliseconds(0);
    let fromEpoch = dateTime.getTime();
    return [fromEpoch, toEpoch];
  }

  queryParamsToString(queryParams: [string, any][]) {
    let queryParamString = "";
    if (queryParams.length > 0) {
      queryParamString = "?";
      queryParams.forEach(queryParamKeyValue => {
        queryParamString += `${queryParamKeyValue[0]}=${queryParamKeyValue[1]}`;
        queryParamString += `&`;
      });
      if (queryParamString.endsWith("&")) {
        queryParamString = queryParamString.replace(/&$/, "");
      }

    }
    return queryParamString;
  }

}
