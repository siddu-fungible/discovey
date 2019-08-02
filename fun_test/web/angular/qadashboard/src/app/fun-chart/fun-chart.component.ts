import {Component, Input, Output, OnChanges, OnInit} from '@angular/core';
import {Chart} from 'angular-highcharts';
import {EventEmitter} from "@angular/core";

@Component({
  selector: 'fun-chart',
  templateUrl: './fun-chart.component.html',
  styleUrls: ['./fun-chart.component.css']
})
export class FunChartComponent implements OnInit, OnChanges {
  @Input() chartType: string = "line";
  @Input() y1Values: any[];
  @Input() xValues: any[];
  @Input() title: string;
  @Input() xAxisLabel: string;
  @Input() y1AxisLabel: string;
  @Input() mileStones: any = null;
  @Input() y1AxisPlotLines: any = null;
  @Input() yMax: number = null;
  @Input() yMin: number = null;
  @Input() public xAxisFormatter: Function;
  @Input() public tooltipFormatter: Function;
  @Input() public pointClickCallback: Function;
  @Output() pointInfo: EventEmitter<any> = new EventEmitter();
  @Input() enableLegend: boolean = true;
  @Input() backgroundColor: string = null;
  @Input() seriesColors: string[] = null;
  @Input() clickUrls;
  @Input() chartHeight;
  chart: any;
  point: any = null;


  constructor() {
  }

  ngOnChanges() {
    var self = this;
    let chartOptions = null;
    if (this.chartType === 'line') {
      chartOptions = {
        chart: {
          type: 'line'
        },
        title: {
          text: this.title,
          useHTML: true
        },
        xAxis: {
          title: {
            text: this.xAxisLabel
          },
          categories: this.xValues,
          labels: {
            formatter: function () {
              if (self.xAxisFormatter)
                return self.xAxisFormatter(this.value);
              else
                return this.value;
            }
          },
        },
        tooltip: {
          formatter: function () {
            if (self.tooltipFormatter)
              return self.tooltipFormatter(this.x, this.y, this.point.metaData);
            else
              return this.y;
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
                  if (self.pointClickCallback) {
                    self.point = self.pointClickCallback(this.category, this.y, this.metaData);
                    self.pointInfo.emit(self.point);
                  }
                }
              }
            }
          }
        },
        series: this.y1Values
      };
      chartOptions.xAxis["plotLines"] = [];
      if (this.mileStones) {
        Object.keys(this.mileStones).forEach((milestone) => {
          chartOptions.xAxis["plotLines"].push({
            color: 'red', // Color value
            dashStyle: 'solid', // Style of the plot line. Default to solid
            value: this.mileStones[milestone], // Value of where the line will appear
            width: 2, // Width of the line
            label: {
              text: milestone,
              verticalAlign: 'top',
              textAlign: 'center'
            }
          });
        });
      }
      if (this.yMax) {
        chartOptions.yAxis["max"] = this.yMax;
      }
      if (this.yMin) {
        chartOptions.yAxis["min"] = this.yMin;
      }
      chartOptions.yAxis["plotLines"] = [];
      if (this.y1AxisPlotLines) {
        for (let dataSet of this.y1AxisPlotLines) {
          if (dataSet.value !== -1) {
            chartOptions.yAxis["plotLines"].push({
              color: 'grey', // Color value
              dashStyle: 'shortdash', // Style of the plot line. Default to solid
              value: dataSet.value, // Value of where the line will appear
              width: 2, // Width of the line
              label: {
                text: dataSet.text,
                align: "right"
              }
            });
          }
        }
      }
      if (this.backgroundColor) {
        chartOptions.chart["backgroundColor"] = this.backgroundColor;
      }
      if (this.seriesColors) {
        chartOptions.colors = this.seriesColors;
        chartOptions.plotOptions.series["lineWidth"] = 1.5;
      }
    } else if (this.chartType === 'vertical_colored_bar_chart') {
      chartOptions = {
        chart: {
          height: this.chartHeight,
          type: "column"
        },
        title: {
          text: this.title,
          useHTML: true

        },
        xAxis: {
          categories: this.xValues,
          labels: {
            style: {
              fontSize: '14px'
            }
          }
        },
        yAxis: {
          min: 0,
          title: {
            text: this.y1AxisLabel
          },
        },
        legend: {
          reversed: true,
          enabled: this.enableLegend
        },
        plotOptions: {
          series: {
            stacking: 'normal',
            pointWidth: 10,
            pointPadding: 0,
            borderWidth: 0,
            groupPadding: 0,
            allowPointSelect: true,
            cursor: 'pointer',
            column: {
              grouping: false
            },
            point: {
              events: {

                click: function () {
                  location.href = self.clickUrls[this.category];
                },

                select: function () {
                  if (self.pointClickCallback) {
                    let metadata = null;
                    let name = null;
                    if (this.series.hasOwnProperty('userOptions')) {
                      if (this.series.userOptions.hasOwnProperty('metadata')) {
                        metadata = this.series.userOptions.metadata;
                      }
                      if (this.series.userOptions.hasOwnProperty('name')) {
                        name = this.series.userOptions.name;
                      }
                    }
                    //self.point = self.pointClickCallback(this.category, this.y, name);
                    self.pointInfo.emit({category: this.category, y: this.y, name: name, metadata: metadata});
                  }
                }
              }
            }

          }
        },
        series: this.y1Values,

        credits: {
          enabled: false
        },
      };
    }

    this.chart = new Chart(chartOptions);
  }

  ngOnInit() {
  }

}
