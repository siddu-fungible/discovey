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
            return ctrl.charting === true;
        }, function (newvalue, oldvalue) {

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
            if(ctrl.chartType === "scatter") {
                for (let i = 0; i < $scope.traceCount; i++) {
                    data.push({
                        x: [],
                        y: [],
                        type: ctrl.chartType,
                        name: ctrl.series[i]

                    });
                }
            } else if(ctrl.chartType === "pie") {
                let values = [];
                let marker = {};
                marker["colors"] = ctrl.colors;
                data.push({values: values,
                    type: ctrl.chartType,
                    labels: ctrl.series,
                    marker: marker});
            }
            if (ctrl.charting) {
                $timeout(function () {
                    Plotly.newPlot("c-" + $scope.genId, data, layout, {displayModeBar: false});
                    $timeout($scope.updatePlot, 10);
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
        };

        $scope.updatePlot = function () {
            //console.log(ctrl.values);
            if(ctrl.chartType === "scatter") {
                let traceList = [];
                for (let i = 0; i < $scope.traceCount; i++) {
                    traceList.push(i);
                }
                let xValueList = [];
                let yValueList = [];

                angular.forEach(ctrl.values, function (value, key) {
                    yValueList.push([parseInt(value)]);
                    xValueList.push([$scope.xValue]);
                });

                let data = {x: xValueList, y: yValueList};
                Plotly.extendTraces("c-" + $scope.genId, data, traceList);

                $scope.xValue += 1;
            } else if(ctrl.chartType === "pie") {
                let traceList = [];
                for (let i = 0; i < $scope.traceCount; i++) {
                    traceList.push(i);
                }
                let values = [];
                angular.forEach(ctrl.values, function (value, key) {
                    values.push(value);
                });
                let marker = {};
                marker["colors"] = ctrl.colors;
                let data = [{values: values, type: ctrl.chartType, labels: ctrl.series, marker: marker}];
                let layout = {};
                if(ctrl.title) {
                    layout["title"] = ctrl.title;
                    layout["titleside"] = "bottom";
                }
                Plotly.purge("c-" + $scope.genId);
                Plotly.plot("c-" + $scope.genId, data, layout);
            }

            if(ctrl.autoUpdate) {
                $timeout($scope.updatePlot, 3000);
            }

        };

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
