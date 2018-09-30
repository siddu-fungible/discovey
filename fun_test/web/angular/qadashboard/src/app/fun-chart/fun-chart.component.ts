import {Component, Input, OnInit} from '@angular/core';
import {Chart} from 'angular-highcharts';

@Component({
  selector: 'fun-chart',
  templateUrl: './fun-chart.component.html',
  styleUrls: ['./fun-chart.component.css']
})
export class FunChartComponent implements OnInit {
  // autoUpdate: any;
  // charting: any;
  // @Input() values: any[];
  // updateChartsNow: any;
  // showLegend: any;
  // series: any;
  // title: any;
  // minimal: any;
  // chartType: any;
  // colors: any;
  // width: any;
  // height: any;
  // xaxisTitle: any;
  // yaxisTitle: any;
  // pointClickCallback: any;
  // xaxisFormatter: any;
  // tooltipFormatter: any;
  //
  // genId: any = null;
  @Input() y1Values: any[];
  @Input() xValues: any[];
  @Input() title: string;
  @Input() xAxisLabel: string;
  @Input() y1AxisLabel: string;
  @Input() public xAxisFormatter: Function;
  @Input() public tooltipFormatter: Function;
  chart: any;

  // @Input() xValues: any[];
  // @Input() yValues: any[];


  add() {
    this.chart.addPoint(Math.floor(Math.random() * 10));
  }

  constructor() {
  }

  ngOnChanges() {
    var self = this;
    this.chart = new Chart({
      chart: {
        type: 'line'
      },
      title: {
        text: this.title
      },
      xAxis: {
        title: {
          text: this.xAxisLabel
        },
        categories: this.xValues,
        labels: {
          formatter: function () {
            return self.xAxisFormatter(this.value);
          }
        },
      },
      tooltip: {
        formatter: function () {
          return self.tooltipFormatter(this.x, this.y);
        }
      },
      yAxis: {
        title: {
          text: this.y1AxisLabel
        }
      },
      credits: {
        enabled: false
      },
      plotOptions: {
        line: {
          animation: false,
          marker: {
            enabled: true
          }
        },
        series: {
          animation: false
        }
      },
      series: this.y1Values
    });
  }

  ngOnInit() {
  }

  // getRandomId() {
  //   if (!this.genId) {
  //     let min = Math.ceil(0);
  //     let max = Math.floor(10000);
  //     this.genId = Math.floor(Math.random() * (max - min + 1)) + min;
  //     return this.genId;
  //   } else {
  //     return this.genId;
  //   }
  // }

}
