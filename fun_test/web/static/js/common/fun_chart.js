(function (angular) {
    'use strict';

    function FunChartController($scope, $http, $element, $timeout, $attrs) {
        let ctrl = this;

        $scope.getRandomId = function () {
            if (!$scope.genId) {
                let min = Math.ceil(0);
                let max = Math.floor(10000);
                $scope.genId = Math.floor(Math.random() * (max - min + 1)) + min;
                return $scope.genId;
            } else {
                return $scope.genId;
            }
        };

        $scope.getRandomId();

        $scope.$watch(function () {
                /*console.log(ctrl.values);*/
                return ctrl.values;
            }
            , function (newvalue, oldvalue) {
                if (newvalue === oldvalue) {
                    return;
                }
                /*ctrl.updateChartsNow = false;*/
                let layout = {
                    showlegend: ctrl.showLegend,
                    autosize: true
                };

                if (ctrl.minimal) {
                    layout["margin"] = {
                        t: 0,
                        l: 0,
                        r: 0,
                        b: 0,
                        pad: 0,
                    }
                }

                if (ctrl.width) {
                    layout["width"] = ctrl.width;
                }

                if (ctrl.height) {
                    layout["height"] = ctrl.height;
                }

                if (ctrl.title) {
                    layout["title"] = ctrl.title;
                    layout["titleside"] = "bottom";

                }

                let data = [];

                if (ctrl.charting) {
                    $timeout(function () {
                        if ((ctrl.chartType === "horizontal_colored_bar_chart") || (ctrl.chartType === "vertical_colored_bar_chart")) {

                            let seriesData = [];
                            let series = ctrl.series.reverse();
                            let colors = [];
                            if(ctrl.colors) {
                                colors = ctrl.colors;
                            } else {

                            }
                            /*, colors: colors.reverse() */
                            colors = colors.reverse();
                            series.forEach(function (seriesName, index) {
                                let oneSeriesDataEntry = {name: seriesName, data: []};
                                angular.forEach(ctrl.values, function (categoryInfo, categoryName) {
                                    if(categoryInfo.hasOwnProperty("Link")) {
                                        oneSeriesDataEntry.point = {
                                            events: {
                                                click: function () {
                                                    location.href = categoryInfo["Link"];
                                                }
                                            }
                                        }

                                    }
                                    oneSeriesDataEntry.data.push(categoryInfo[seriesName]);
                                    if (ctrl.colors) {
                                        oneSeriesDataEntry.color = colors[index];
                                    }
                                });
                                seriesData.push(oneSeriesDataEntry);
                            });

                            let categories = Object.keys(ctrl.values);

                            let thisChartType = 'bar';
                            if(ctrl.chartType === "vertical_colored_bar_chart") {
                                thisChartType = "column";
                            }

                            Highcharts.chart("c-" + $scope.genId, {
                                chart: {
                                    type: thisChartType,
                                    height: ctrl.height,
                                    width: ctrl.width
                                },
                                title: {
                                    text: ctrl.title
                                },
                                xAxis: {
                                    categories: categories,
                                    labels: {
                                        style: {
                                            fontSize: '14px'
                                        }
                                    }
                                },
                                yAxis: {
                                    min: 0,
                                    max: 100,
                                    title: {
                                        text: ctrl.yaxisTitle
                                    },
                                },
                                legend: {
                                    reversed: true
                                },
                                plotOptions: {
                                    series: {
                                        stacking: 'normal',
                                        pointWidth: 20,
                                        pointPadding: 0,
                                        borderWidth: 0,
                                        groupPadding: 0,

                                    }
                                },
                                series: seriesData,

                                credits: {
                                    enabled: false
                                },
                            });
                        } else if (ctrl.chartType === "pie") {

                            let plotData = [];
                            ctrl.series.forEach(function (seriesName) {
                                let oneEntry = {};
                                oneEntry.name = seriesName;
                                oneEntry.y = ctrl.values[seriesName];
                                plotData.push(oneEntry);
                            });

                            Highcharts.chart("c-" + $scope.genId, {
                                chart: {
                                    plotBackgroundColor: null,
                                    plotBorderWidth: null,
                                    plotShadow: false,
                                    type: 'pie',
                                    height: ctrl.height,
                                    width: ctrl.width
                                },
                                title: {
                                    text: ctrl.title
                                },
                                tooltip: {
                                    pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
                                },
                                plotOptions: {
                                    pie: {
                                        allowPointSelect: true,
                                        cursor: 'pointer'
                                    },
                                },
                                credits: {
                                    enabled: false
                                },
                                series: [{
                                    name: ctrl.title,
                                    colorByPoint: true,
                                    data: plotData,
                                    colors: ctrl.colors
                                }]
                            });
                        } else if (ctrl.chartType === "line-chart") {
                            let series = angular.copy(ctrl.values);
                            let chartInfo = {
                                chart: {
                                    height: ctrl.height,
                                    width: ctrl.width
                                },
                                title: {
                                    text: ctrl.title
                                },

                                subtitle: {
                                    text: ''
                                },
                                xAxis: {
                                    categories: ctrl.series,
                                    title: {
                                        text: ctrl.xaxisTitle
                                    }
                                },

                                yAxis: {
                                    title: {
                                        text: ctrl.yaxisTitle
                                    }
                                },
                                legend: {
                                    layout: 'vertical',
                                    align: 'right',
                                    verticalAlign: 'middle'
                                },
                                credits: {
                                    enabled: false
                                },
                                plotOptions: {
                                    series: {
                                        animation: false,
                                        label: {
                                            connectorAllowed: false
                                        },
                                        point: {
                                            events: {
                                                click: function (e) {
                                                    /*location.href = 'https://en.wikipedia.org/wiki/' +
                                                        this.options.key;*/
                                                    console.log(ctrl.pointClickCallback);
                                                    ctrl.pointClickCallback()(e.point);
                                                }
                                            }
                                        }
                                    }

                                },

                                series: series,


                                responsive: {
                                    rules: [{
                                        condition: {
                                            maxWidth: 500
                                        },
                                        chartOptions: {
                                            legend: {
                                                layout: 'horizontal',
                                                align: 'center',
                                                verticalAlign: 'bottom'
                                            }
                                        }
                                    }]
                                }

                            };
                            try {
                                if (ctrl.xaxisFormatter && ctrl.xaxisFormatter()()) {
                                    chartInfo.xAxis["labels"] = {formatter: function () {
                                        return ctrl.xaxisFormatter()(this.value);
                                    }};
                                }

                                if (ctrl.tooltipFormatter && ctrl.tooltipFormatter()()) {
                                    chartInfo.tooltip = {
                                        formatter: function () {
                                            return ctrl.tooltipFormatter()(this.x, this.y);
                                        }
                                    }
                                }

                                if (ctrl.pointClickCallback && ctrl.pointClickCallback()()) {
                                    chartInfo.plotOptions.series["point"] = {
                                        events: {
                                            click: function (e) {
                                                ctrl.pointClickCallback()(e.point);
                                            }
                                        }
                                    }
                                }
                            } catch (e) {

                            }


                            Highcharts.chart("c-" + $scope.genId, chartInfo);
                        } else if (ctrl.chartType === "solidguage") {
                            Highcharts.chart("c-" + $scope.genId, {
                                chart: {
                                    type: 'solidgauge',
                                    height: ctrl.height,
                                    width: ctrl.width
                                },

                                title: {
                                    text: 'Performance goals'
                                },
                                credits: {
                                    enabled: false
                                },

                                tooltip: {
                                    borderWidth: 0,
                                    backgroundColor: 'none',
                                    shadow: false,
                                    style: {
                                        fontSize: '16px'
                                    },
                                    pointFormat: '{series.name}<br><span style="font-size:2em; color: {point.color}; font-weight: bold">{point.y}%</span>',
                                    positioner: function (labelWidth) {
                                        return {
                                            x: (this.chart.chartWidth - labelWidth) / 2,
                                            y: (this.chart.plotHeight / 2) + 15
                                        };
                                    }
                                },

                                pane: {
                                    startAngle: 0,
                                    endAngle: 360,
                                    background: [{
                                        outerRadius: '112%',
                                        innerRadius: '88%',
                                        backgroundColor: Highcharts.Color(Highcharts.getOptions().colors[0])
                                            .setOpacity(0.3)
                                            .get(),
                                        borderWidth: 0
                                    }, {
                                        outerRadius: '87%',
                                        innerRadius: '63%',
                                        backgroundColor: Highcharts.Color(Highcharts.getOptions().colors[1])
                                            .setOpacity(0.3)
                                            .get(),
                                        borderWidth: 0
                                    }, {
                                        outerRadius: '62%',
                                        innerRadius: '38%',
                                        backgroundColor: Highcharts.Color(Highcharts.getOptions().colors[2])
                                            .setOpacity(0.3)
                                            .get(),
                                        borderWidth: 0
                                    }]
                                },

                                yAxis: {
                                    min: 0,
                                    max: 100,
                                    lineWidth: 0,
                                    tickPositions: []
                                },

                                plotOptions: {
                                    solidgauge: {
                                        dataLabels: {
                                            enabled: false
                                        },
                                        linecap: 'round',
                                        stickyTracking: false,
                                        rounded: true
                                    }
                                },
                                legend: {
                                    labelFormatter: function () {
                                        return '<span style="color:' + this.data[0].color + '">' + this.name + '</span>';
                                    },
                                    symbolWidth: 0
                                },

                                series: [{
                                    name: 'Networking',
                                    data: [{
                                        color: Highcharts.getOptions().colors[0],
                                        radius: '112%',
                                        innerRadius: '88%',
                                        y: 80
                                    }],
                                    showInLegend: true

                                }, {
                                    name: 'Storage',
                                    data: [{
                                        color: Highcharts.getOptions().colors[1],
                                        radius: '87%',
                                        innerRadius: '63%',
                                        y: 65
                                    }],
                                    showInLegend: true,
                                    events: {
                                        click: function () {
                                            location.href = "/metrics/view_all_storage_charts";
                                            location.target = "_blank";
                                        }
                                    }

                                }, {
                                    name: 'Crypto',
                                    data: [{
                                        color: Highcharts.getOptions().colors[2],
                                        radius: '62%',
                                        innerRadius: '38%',
                                        y: 50
                                    }],
                                    showInLegend: true
                                }]
                            })
                        }
                        /*$timeout($scope.updatePlot, 10);*/
                    }, 10);

                }
            }, true);

        ctrl.$onInit = function () {

            //["Sent", "Received"];
            $scope.xValue = 0;
            $scope.values = {};
            angular.forEach(ctrl.series, function (input) {
                $scope.values[input] = [];
            });

            /*$timeout($scope.repeat, 1000);*/


        };

        $scope.repeat = function () {
            console.log(ctrl);
            $timeout($scope.repeat, 1000);
        }

    }


    angular.module('qa-dashboard').component('funChart', {
        template: '<div class="fun-chart" id="c-{{ genId }}">\n' +
        '\n' +
        '</div>\n',
        controller: FunChartController,
        bindings: {
            autoUpdate: '<',
            charting: '<',
            values: '<',
            updateChartsNow: '=',
            showLegend: '<',
            series: '<',
            title: '<',
            minimal: '<',
            chartType: '@',
            colors: '<',
            width: '<',
            height: '<',
            xaxisTitle: '<',
            yaxisTitle: '<',
            pointClickCallback: '&',
            xaxisFormatter: '&',
            tooltipFormatter: '&'
        }
    });

})(window.angular);
