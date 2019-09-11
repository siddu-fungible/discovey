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
      return () => {
      };
    })
  }

  convertToLocalTimezone(t): Date {
    let d = new Date(t.replace(/\s+/g, 'T'));
    let epochValue = d.getTime();
    return new Date(epochValue);
  }

  changeToPstTimezone(date) {
    let pstDate = new Date(date.toLocaleString('en-US', {
      timeZone: "America/Los_Angeles"
    }));
    return pstDate;
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

}
