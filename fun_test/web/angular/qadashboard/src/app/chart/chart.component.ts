import { Component, OnInit } from '@angular/core';
import { Chart } from 'angular-highcharts';
import { ApiService} from "../services/api/api.service";

@Component({
  selector: 'app-fun-chart',
  template: `
    <button (click)="add()">Add Point!</button>
    <div [chart]="chart"></div>
  `
})
export class ChartComponent implements OnInit {
  ngOnInit() {
    // this.doSomething1();

  }
  constructor(private apiService: ApiService) {

  }

  chart = new Chart({
    chart: {
      type: 'line'
    },
    title: {
      text: 'Linechart'
    },
    credits: {
      enabled: false
    },
    series: [
      {
        name: 'Line 1',
        data: [1, 2, 3]
      }
    ]
  });
  doSomething1(): void {
    console.log("Doing Something1");
    let payload = {"metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"]};
    this.apiService.post('/metrics/scores', payload).subscribe(response => {
        console.log(response.data);
        this.delay(1000);
      },
      error => {
        console.log(error);
        this.delay(1000);

      });
  }

   async delay(ms: number) {
    await new Promise(resolve => setTimeout(()=>resolve(), ms)).then(()=> {
            this.add();
        this.doSomething1();
      console.log("fired")
    });
}
r() {
   return Math.random();
}


  // add point to chart serie
  add() {
    this.chart.addPoint(Math.floor(Math.random() * 10));
  }
}
