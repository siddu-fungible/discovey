import {Component, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";

@Component({
  selector: 'app-performance',
  templateUrl: './performance.component.html',
  styleUrls: ['./performance.component.css']
})
export class PerformanceComponent implements OnInit {

  constructor(private apiService: ApiService) {

  }

  private componentState: string = "Unknown";

  ngOnInit() {

  }

  doSomething1(): void {
    console.log("Doing Something1");
    let payload = {"metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"]};
    this.apiService.post('/metrics/scores', payload).subscribe(response => {
        console.log(response.data);
        this.componentState = response.message;
      },
      error => {
        console.log(error);
        this.componentState = "Error";
      });

  }

  getComponentState(): string {
    return this.componentState;
  }

}
