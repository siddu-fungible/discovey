import {Component, OnInit} from '@angular/core';
import {ApiService} from "../api.service";

@Component({
  selector: 'app-performance',
  templateUrl: './performance.component.html',
  styleUrls: ['./performance.component.css']
})
export class PerformanceComponent implements OnInit {

  constructor(private apiService: ApiService) {

  }

  ngOnInit() {

    let payload = {"metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"]};
    this.apiService.post('/metrics/scores', payload).subscribe(response => {
        console.log(response.data);
      },
      error => {
        console.log(error);
      });
    this.apiService.post('/metrics/7scores', payload).subscribe(response => {
        console.log(response.data);
      },
      error => {
        console.log(error);
      });


  }

}
