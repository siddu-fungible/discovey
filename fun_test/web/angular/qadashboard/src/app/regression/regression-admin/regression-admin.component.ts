import { Component, OnInit } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";

@Component({
  selector: 'app-regression-admin',
  templateUrl: './regression-admin.component.html',
  styleUrls: ['./regression-admin.component.css']
})
export class RegressionAdminComponent implements OnInit {
  info = {};
  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

  ngOnInit() {
    this.fetchInfo();
  }

  fetchInfo() {
    this.apiService.get("/regression/modules").subscribe((response) => {
      console.log(response);
      let modules = response.data;
      modules.forEach((module) => {
        this.info[module.name] = {name: module.name, verboseName: module.verbose_name};

      })
    }, error => {
      this.loggerService.error("Error fetching modules");
    })
  }

  fetchScriptInfo(moduleName, moduleInfo) {

  }

}
