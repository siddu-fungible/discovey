import {Component, Input, OnInit} from '@angular/core';
import { Chart } from 'angular-highcharts';

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
  chart: any;

  // @Input() xValues: any[];
  // @Input() yValues: any[];


  add() {
    this.chart.addPoint(Math.floor(Math.random() * 10));
  }

  constructor() {
  }

  ngOnChanges() {
    this.chart = new Chart({
    chart: {
      type: 'line',
      width: 500,
      height: 500
    },
    title: {
      text: this.title
    },
    xAxis: {
      title: {
        text: this.xAxisLabel
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
//
//                 if (ctrl.charting) {
//                     $timeout(function () {
//                          if (ctrl.chartType === "line-chart") {
//                             let series = angular.copy(ctrl.values);
//                             let chartInfo = {
//                                 chart: {
//                                     height: ctrl.height,
//                                     width: ctrl.width
//                                 },
//                                 title: {
//                                     text: ctrl.title
//                                 },
//
//                                 subtitle: {
//                                     text: ''
//                                 },
//                                 xAxis: {
//                                     categories: ctrl.series,
//                                     title: {
//                                         text: ctrl.xaxisTitle
//                                     }
//                                 },
//
//                                 yAxis: {
//                                     title: {
//                                         text: ctrl.yaxisTitle
//                                     }
//                                 },
//                                 legend: {
//                                     layout: 'vertical',
//                                     align: 'right',
//                                     verticalAlign: 'middle'
//                                 },
//                                 credits: {
//                                     enabled: false
//                                 },
//                                 plotOptions: {
//                                     line: {
//                                         animation: false,
//                                         marker: {
//                                             enabled: true
//                                         }
//                                     },
//                                     series: {
//                                         animation: false,
//                                         label: {
//                                             connectorAllowed: false
//                                         },
//                                         point: {
//                                             events: {
//                                                 click: function (e) {
//                                                     /*location.href = 'https://en.wikipedia.org/wiki/' +
//                                                         this.options.key;*/
//                                                     console.log(ctrl.pointClickCallback);
//                                                     ctrl.pointClickCallback()(e.point);
//                                                 }
//                                             }
//                                         }
//                                     }
//
//                                 },
//
//                                 series: series,
//
//
//                                 responsive: {
//                                     rules: [{
//                                         condition: {
//                                             maxWidth: 500
//                                         },
//                                         chartOptions: {
//                                             legend: {
//                                                 layout: 'horizontal',
//                                                 align: 'center',
//                                                 verticalAlign: 'bottom'
//                                             }
//                                         }
//                                     }]
//                                 }
//
//                             };
//                             try {
//                                 if (ctrl.xaxisFormatter && ctrl.xaxisFormatter()()) {
//                                     chartInfo.xAxis["labels"] = {formatter: function () {
//                                         return ctrl.xaxisFormatter()(this.value);
//                                     }};
//                                 }
//
//                                 if (ctrl.tooltipFormatter && ctrl.tooltipFormatter()()) {
//                                     chartInfo.tooltip = {
//                                         formatter: function () {
//                                             return ctrl.tooltipFormatter()(this.x, this.y);
//                                         }
//                                     }
//                                 }
//
//                                 if (ctrl.pointClickCallback && ctrl.pointClickCallback()()) {
//                                     chartInfo.plotOptions.series["point"] = {
//                                         events: {
//                                             click: function (e) {
//                                                 ctrl.pointClickCallback()(e.point);
//                                             }
//                                         }
//                                     }
//                                 }
//                             } catch (e) {
//                                 console.log(e);
//
//                             }
//
//
//                             Highcharts.chart("c-" + $scope.genId, chartInfo);
//                         } }, 10);
//
//                 }
//             }, true);
//
//         ctrl.$onInit = function () {
//
//             //["Sent", "Received"];
//             $scope.xValue = 0;
//             $scope.values = {};
//             angular.forEach(ctrl.series, function (input) {
//                 $scope.values[input] = [];
//             });
//
//             /*$timeout($scope.repeat, 1000);*/
//
//
//         };
//
//         $scope.repeat = function () {
//             console.log(ctrl);
//             $timeout($scope.repeat, 1000);
//         }
//
//     }
//             autoUpdate: '<',
//             charting: '<',
//             values: '<',
//             updateChartsNow: '=',
//             showLegend: '<',
//             series: '<',
//             title: '<',
//             minimal: '<',
//             chartType: '@',
//             colors: '<',
//             width: '<',
//             height: '<',
//             xaxisTitle: '<',
//             yaxisTitle: '<',
//             pointClickCallback: '&',
//             xaxisFormatter: '&',
//             tooltipFormatter: '&'
//         }
//     });
//
// })(window.angular);
