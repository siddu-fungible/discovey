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


            if(ctrl.title) {
                layout["title"] = ctrl.title;
            }

            let data = [];
            for (let i = 0; i < $scope.traceCount; i++) {
                data.push({
                    x: [],
                    y: [],
                    type: 'scatter',
                    name: ctrl.series[i]

                });
            }
            if (ctrl.charting) {
                Plotly.newPlot("c-" + $scope.genId, data, layout, {displayModeBar: false});
                $timeout($scope.updatePlot, 5000);
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
            if (ctrl.charting) {
                Plotly.extendTraces("c-" + $scope.genId,
                    data, traceList);
                $timeout($scope.updatePlot, 5000);
            }
            $scope.xValue += 1;
        };

    }

    angular.module('tools').component('funChart', {
        templateUrl: '/static/fun_chart.html',
        controller: FunChartController,
        bindings: {
            syncing: '<',
            charting: '<',
            values: '<',
            showLegend: '<',
            series: '<',
            title: '<',
            minimal: '<'
        }
    });

})(window.angular);
