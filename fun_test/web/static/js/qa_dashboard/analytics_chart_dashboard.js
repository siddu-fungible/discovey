'use strict';

function AnalyticsChartDashboardController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        console.log("AnalyticsChartDashboardController");
        $scope.chart1Name = "BLT Performance IOPS";
        $scope.model1Name = "PerformanceBlt";
        $scope.chart2Name = "BLT Write IOPS";
        $scope.model2Name = "VolumePerformance";
        $scope.chart3Name = "BLT Write Latency";
        $scope.model3Name = "VolumePerformance";
    };

}

angular.module('qa-dashboard').controller("analyticsChartDashboardController", AnalyticsChartDashboardController);
