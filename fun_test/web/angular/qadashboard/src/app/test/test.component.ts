import { Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2 } from '@angular/core';
import { ApiService } from "../services/api/api.service";
import { LoggerService } from "../services/logger/logger.service";
import { from, Observable, of } from "rxjs";
import { mergeMap, switchMap } from "rxjs/operators";
import { CommonService } from "../services/common/common.service";
import { RegressionService } from "../regression/regression.service";
import { Announcement } from "./announcement";


@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})

export class TestComponent implements OnInit {

  levels = ['1','2'];

  announcementModel = new Announcement('test message', '1');



  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService, private regressionService: RegressionService) {
  }


  ngOnInit() {

  }

  onSubmit() {
    this.apiService.get('/api/v1/site_configs').subscribe((response) =>{
      console.log("success");
    }, error => {
      this.logger.error("Unable to fetch announcements");
    });
  }
}


