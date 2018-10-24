import { Component, OnInit } from '@angular/core';
import {CommonService} from "../services/common/common.service";
import {ApiService} from "../services/api/api.service";

export enum HttpMethod {
  GET = "GET",
  POST = "POST",
  DELETE = "DELETE",
  PUT = "PUT"
}

export class ApiLog {
  method: HttpMethod;
  text: string;
  url: string;
  id: string;
}

@Component({
  selector: 'app-api-viewer',
  templateUrl: './api-viewer.component.html',
  styleUrls: ['./api-viewer.component.css']
})
export class ApiViewerComponent implements OnInit {
  apiLogs: ApiLog[];
  buttonColors = {"GET": "button-color-get", "POST": "button-color-post", "DELETE": "button-color-delete", "PUT": "button-color-put"};
  constructor(private apiService: ApiService) { }

  ngOnInit() {

  }


  getButtonColorClass(method: string): string {
    return this.buttonColors[method];
  }

  refresh() {
    this.apiLogs = [...this.apiService.getApiLogs()];
    let i = 0;
  }


  getJson(o) {
    return JSON.stringify(o, null, 4);
  }



}
