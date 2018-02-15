'use strict';

function AnalyticsTablesController($scope, $http, commonService, $timeout) {
    let ctrl = this;

    ctrl.$onInit = function () {
    };

    ctrl.$postLink = function () {

        console.log($scope.metricModelName);
        console.log($scope.chartName);
        $scope.fetchTableData();
    };

    $scope.fetchTableData = () => {
        let payload = {};
        payload["metric_model_name"] = $scope.metricModelName;
        payload["chart_name"] = $scope.chartName;
        commonService.apiPost("/metrics/table_data", payload, "fetchTableData").then((data) => {

        });
    };

    $scope.test = () => {
        console.log($scope.metricModelName);

    }

}



angular.module('qa-dashboard').controller("analyticsTablesController", AnalyticsTablesController);
