import { Component, OnInit, OnChanges } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";

@Component({
  selector: 'app-script-history',
  templateUrl: './script-history.component.html',
  styleUrls: ['./script-history.component.css']
})
export class ScriptHistoryComponent implements OnInit {
  scriptId: number = null;
  scriptPath: string = null;
  filterData = [];
  constructor(private apiService: ApiService, private loggerService: LoggerService, private route: ActivatedRoute) { }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['scriptId']) {
        this.scriptId = params['scriptId'];
      }
    });
    this.fetchHistory();
  }

  fetchHistory() {
    let payload = {pk: this.scriptId};
    this.apiService.post('/regression/script', payload).subscribe(response => {
      this.scriptPath = response.data.script_path;
      let i = 0;
      this.filterData.push({info: this.scriptPath, payload: {script_path: this.scriptPath}});

    }, error => {
      this.loggerService.error("/regression/script");
    })
  }



}
