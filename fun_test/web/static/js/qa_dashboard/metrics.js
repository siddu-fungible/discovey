'use strict';

function MetricsController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.fetchMetricsList();
    };

    $scope.fetchMetricsList = function () {
        commonService.apiGet("/metrics/metrics_list", "fetchMetricsList").then(function(data) {
            let i = 0;
        });
    }
}

angular.module('qa-dashboard').controller("metricsController", MetricsController);


