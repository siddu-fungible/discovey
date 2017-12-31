(function (angular) {
    'use strict';

    function FunChartController($scope, $http, $element, $timeout) {
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
                return ctrl.updateChartsNow === true;
            }
            , function (newvalue, oldvalue) {
            if(newvalue === oldvalue) {
                return;
            }
            ctrl.updateChartsNow = false;
            let layout = {
                showlegend: ctrl.showLegend,
                autosize: true
            };

            if(ctrl.minimal) {
                layout["margin"] = {
                    t: 0,
                    l: 0,
                    r: 0,
                    b: 0,
                    pad: 0,
                }
            }

            if(ctrl.width) {
                layout["width"] = ctrl.width;
            }

            if(ctrl.height) {
                layout["height"] = ctrl.height;
            }

            if(ctrl.title) {
                layout["title"] = ctrl.title;
                layout["titleside"] = "bottom";

            }

            let data = [];

            if (ctrl.charting) {
                $timeout(function () {
                    if(ctrl.chartType === "horizontal_colored_bar_chart") {

                        let seriesData = [];
                        let series = ctrl.series.reverse();
                        series.forEach(function(seriesName, index){
                            let oneSeriesDataEntry = {name: seriesName, data: [], colors: ctrl.colors.reverse()};
                            angular.forEach(ctrl.values, function (categoryInfo, categoryName) {
                                oneSeriesDataEntry.data.push(categoryInfo[seriesName]);
                                oneSeriesDataEntry.color = ctrl.colors[index];
                            });
                            seriesData.push(oneSeriesDataEntry);
                        });

                        let categories = Object.keys(ctrl.values);

                        Highcharts.chart("c-" + $scope.genId, {
                            chart: {
                                type: 'bar',
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
                                    text: 'Percentage'
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
                            series: seriesData
                        });
                    } else if(ctrl.chartType === "pie") {

                        let plotData = [];
                        ctrl.series.forEach(function(seriesName){
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
                            }
                        },
                        series: [{
                            name: ctrl.title,
                            colorByPoint: true,
                            data: plotData,
                            colors: ctrl.colors
                        }]
                    });
                    }
                    /*$timeout($scope.updatePlot, 10);*/
                }, 1000);

            }
        }, true);

        ctrl.$onInit = function () {

             //["Sent", "Received"];
            $scope.traceCount = ctrl.series.length;
            $scope.xValue = 0;
            $scope.values = {};
            angular.forEach(ctrl.series, function (input) {
                $scope.values[input] = [];
            });

            /*$timeout($scope.repeat, 1000);*/


        };

        $scope.repeat = function() {
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
            title: '@',
            minimal: '<',
            chartType: '@',
            colors: '<',
            width: '@',
            height: '@'
        }
    });

})(window.angular);
