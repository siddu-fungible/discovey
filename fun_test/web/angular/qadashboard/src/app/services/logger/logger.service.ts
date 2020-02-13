import { Injectable } from '@angular/core';
import {Toast, ToasterService} from "angular2-toaster";
import {CommonService} from "../common/common.service";
import * as StackTrace from 'stacktrace-js';


export let isDebugMode = true;


export enum LogDataType {
  SIMPLE = 1,
  API = 2
}

export enum AlertLevel {
  SUCCESS = "Success",
  ERROR = "Error"
}

export class Log {
  timestamp: number;
  data: any;
  dataType: LogDataType;
  alertLevel: AlertLevel;
  public constructor(
      timestamp?: number,
      data?: any,
      dataType?: LogDataType,
      alertLevel?: AlertLevel
  ) {
    this.timestamp = timestamp;
    this.data = data;
    this.dataType = dataType;
    this.alertLevel = alertLevel;
  }
}

@Injectable({
  providedIn: 'root',
})
export class LoggerService {

  logs: Log [] = [];
  constructor(private toasterService: ToasterService, private commonService: CommonService) {
  }

  addLog (log: Log): void {
    if (!log.timestamp) {
      log.timestamp = new Date().getTime();
    }
    this.logs.push(log);
    if (log.alertLevel === AlertLevel.ERROR) {
      this.commonService.setAlert();
    }
  }

  formatErrorObject(error) {
    let output = "";
    if (error.hasOwnProperty('message')) {
      output += `Message: ${error.message}\n`;
    }
    if (error.hasOwnProperty('stack')) {
      let stackLines = error.stack.split('\n');
      stackLines.forEach(stackLine => output += `${stackLine}\n`);
    }
    return output;
  }

  error(args: any, errorObject?) {


    var errback = function(err) { console.log(err.message); };
    StackTrace.get().then((stackFrames) => {
      console.error(args);
      console.error(stackFrames);
      let message = args;
      let toasterMessage = message;

      if (errorObject) {
        if (errorObject.hasOwnProperty('message')) {
          toasterMessage += ": " + errorObject.message;
        }
        if (errorObject.hasOwnProperty('value') && errorObject.value.hasOwnProperty('error_message')) {
          toasterMessage += ": " + errorObject.value.error_message;
        } else if (errorObject.hasOwnProperty('value')) {
          toasterMessage += ": " + errorObject.value;
        }
        message += "\n";
        message += this.formatErrorObject(errorObject);
      }
      let toast: Toast = {
        type: 'error',
        title: toasterMessage,
        showCloseButton: true,
        timeout: 0
      };
      this.toasterService.pop(toast);
      let plainLog = new Log(null, message, LogDataType.SIMPLE, AlertLevel.ERROR);
      this.addLog(plainLog);

    }).catch(errback);

  }


  success(text: string) {
    let toast: Toast = {
      type: 'success',
      title: text,
      showCloseButton: true,
      timeout: 3000
    };
    this.toasterService.pop(toast);
    let plainLog = new Log(null, text, LogDataType.SIMPLE, AlertLevel.SUCCESS);
    this.addLog(plainLog);
  }

}
