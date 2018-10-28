import { Component, OnInit } from '@angular/core';
import {ControllerElement} from "../storage-controller/storage-controller.component";
import {ApiService} from "../services/api/api.service";
import {CommonService} from "../services/common/common.service";
import {Controller} from "../services/common/common.service";

@Component({
  selector: 'app-demo1',
  templateUrl: './demo1.component.html',
  styleUrls: ['./demo1.component.css']
})
export class Demo1Component implements OnInit {

  sideBarClass: boolean = false;
  showingApiViewer: boolean = true;
  controller: Controller = null;

  constructor(private apiService: ApiService, private commonService: CommonService) {
  }

  ngOnInit() {
    this.checkControllerStatus();
  }

  sideBarCollapseClick() {
    this.sideBarClass = !this.sideBarClass;
  }

  checkControllerStatus() {
    this.apiService.get("/demo/get_controllers", false).subscribe((response) => {
      let controllers = response.data;
      controllers.forEach((controller) => {

        let newController = new Controller();
        newController.ip = controller.ip;
        newController.port = controller.port;
        this.commonService.setActiveController(newController);
        this.controller = newController;
        this.healthCheck();
      });
      setTimeout(()=> {this.checkControllerStatus()}, 10000);
    }, error => {
      setTimeout(()=> {this.checkControllerStatus()}, 10000);
      this.controller = null;

    });

  }

  healthCheck() {

      let url = this.commonService.getBaseUrl() + "/api_server/health";
      this.apiService.get(url, false).subscribe((response) => {
        console.log(response);
        this.controller.health = response.message === "healthy";
      }, error => {
        this.controller.health = false;
      });
      //console.log(data);
    };

}
