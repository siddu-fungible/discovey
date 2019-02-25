import { Component, OnInit } from '@angular/core';
import {ApiService} from "../services/api/api.service";

interface SessionLogInterface {
  
}

class SessionLog implements SessionLogInterface {

}

@Component({
  selector: 'app-alerts',
  templateUrl: './alerts.component.html',
  styleUrls: ['./alerts.component.css']
})
export class AlertsComponent implements OnInit {

  sessionLogs: any = [];
  constructor(private apiService: ApiService) { }

  ngOnInit() {
    let url = "/common/get_session_logs";
    this.apiService.get(url).subscribe(response => {
      let i = 0;
    })
  }

}
