import { Component, OnInit } from '@angular/core';
import {LoggerService, Log, LogDataType, AlertLevel} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";

@Component({
  selector: 'app-log-viewer',
  templateUrl: './log-viewer.component.html',
  styleUrls: ['./log-viewer.component.css']
})
export class LogViewerComponent implements OnInit {
  logs: Log [] = [];
  LogDataType = LogDataType;
  AlertLevel = AlertLevel;


  constructor(private loggerService: LoggerService, private commonService: CommonService) { }

  ngOnInit() {
    this.commonService.clearAlert();
    this.fetchLogs();
  }

  fetchLogs() {
    this.logs = this.loggerService.logs;
  }

  timestampToDate(timestamp) {
    let d = this.commonService.timestampToDate(timestamp);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString();
  }

  objectToJson(o) {
    return JSON.stringify(o);
  }
}
