import { Component, OnInit } from '@angular/core';
import {Daemon} from "./definitions";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";

@Component({
  selector: 'app-daemons',
  templateUrl: './daemons.component.html',
  styleUrls: ['./daemons.component.css']
})
export class DaemonsComponent implements OnInit {
  daemons: Daemon [];
  constructor(private loggerService: LoggerService, private commonService: CommonService) { }

  ngOnInit() {
    new Daemon().getAll().subscribe(response => {
      this.daemons = response
    }, error => {
      this.loggerService.error("Unable initialize daemons");
    });
  }

  getPrettyTime(epochValue) {
    return this.commonService.getPrettyPstTime(this.commonService.convertEpochToDate(epochValue));
  }

}
