import { Injectable } from '@angular/core';
import {Toast, ToasterService} from "angular2-toaster";
import {CommonService} from "../common/common.service";


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

  error(args: any) {

    let stack = (new Error).stack;
    //console.error.bind(console, arguments);
    let message = stack + args;
    console.error(message);
    let toast: Toast = {
      type: 'error',
      title: args,
      showCloseButton: true,
      timeout: 0
    };
    this.toasterService.pop(toast);
    let plainLog = new Log(null, args, LogDataType.SIMPLE, AlertLevel.ERROR);
    this.addLog(plainLog);
  }


  success(text: string) {
    let toast: Toast = {
      type: 'success',
      title: text,
      showCloseButton: true,
      timeout: 3
    };
    this.toasterService.pop(toast);
    let plainLog = new Log(null, text, LogDataType.SIMPLE, AlertLevel.SUCCESS);
    this.addLog(plainLog);
  }

}
