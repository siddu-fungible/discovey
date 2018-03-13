'use strict';

function SystemChartsController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.chart1Name = "Best time for 1 malloc/free (WU)";
        $scope.model1Name = "AllocSpeedPerformance";
        $scope.chart2Name = "Best time for 1 malloc/free (Threaded)";
        $scope.model2Name = "AllocSpeedPerformance";
    };

}

angular.module('qa-dashboard').controller("systemChartsController", SystemChartsController);
