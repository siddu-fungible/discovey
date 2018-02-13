'use strict';

function AnalyticsChartDashboardController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        console.log("AnalyticsChartDashboardController");
        $scope.chart1Name = "BLT Performance IOPS";
        $scope.model1Name = "PerformanceBlt";
        $scope.chart2Name = "BLT Performance Latency";
        $scope.model2Name = "PerformanceBlt";
        $scope.chart3Name = "IKV Performance";
        $scope.model3Name = "PerformanceIkv";
    };

}

angular.module('qa-dashboard').controller("analyticsChartDashboardController", AnalyticsChartDashboardController)
