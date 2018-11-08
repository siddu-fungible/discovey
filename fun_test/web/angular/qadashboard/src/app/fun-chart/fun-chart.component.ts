import {Component, Input, Output, OnChanges, OnInit} from '@angular/core';
import {Chart} from 'angular-highcharts';
import {EventEmitter} from "@angular/core";

@Component({
  selector: 'fun-chart',
  templateUrl: './fun-chart.component.html',
  styleUrls: ['./fun-chart.component.css']
})
export class FunChartComponent implements OnInit, OnChanges {
  @Input() y1Values: any[];
  @Input() xValues: any[];
  @Input() title: string;
  @Input() xAxisLabel: string;
  @Input() y1AxisLabel: string;
  @Input() mileStoneIndex: number = null;
  @Input() public xAxisFormatter: Function;
  @Input() public tooltipFormatter: Function;
  @Input() public pointDetail: Function;
  @Output() pointInfo: EventEmitter<any> = new EventEmitter();
  chart: any;
  point: any = null;

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
            allowPointSelect: true,
            cursor: 'pointer',
            point: {
                events: {
                    select: function () {
                        self.point = self.pointDetail(this.category, this.y);
                        self.pointInfo.emit(self.point);
                    }
                }
            }
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
