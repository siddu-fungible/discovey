import {Component, Input, OnInit} from '@angular/core';
import {Chart} from 'angular-highcharts';

@Component({
  selector: 'fun-chart',
  templateUrl: './fun-chart.component.html',
  styleUrls: ['./fun-chart.component.css']
})
export class FunChartComponent implements OnInit {
  @Input() y1Values: any[];
  @Input() xValues: any[];
  @Input() title: string;
  @Input() xAxisLabel: string;
  @Input() y1AxisLabel: string;
  @Input() mileStoneIndex: number = null;
  @Input() public xAxisFormatter: Function;
  @Input() public tooltipFormatter: Function;
  chart: any;

  constructor() {
  }

  ngOnChanges() {
    var self = this;
    let chartOptions = {
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
    };
    if (this.mileStoneIndex) {
      chartOptions.xAxis["plotLines"] = [{
        color: 'red', // Color value
        dashStyle: 'solid', // Style of the plot line. Default to solid
        value: this.mileStoneIndex, // Value of where the line will appear
        width: 2, // Width of the line
        label: {
          text: 'Tape-out',
          verticalAlign: 'top',
          textAlign: 'center'
        }
      }];
    }
    this.chart = new Chart(chartOptions);
  }

  ngOnInit() {
  }

}
