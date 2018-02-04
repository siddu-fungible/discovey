'use strict';

function MetricsController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.metricsList = [];
        $scope.fetchMetricsList();
        $scope.currentTableFields = null;
        $scope.fetchChartList("Performance1");
        $scope.fetchChartsInfo("Performance1");
        $scope.fetchMetricsData("Performance1", "Chart 1")
    };

    $scope.fetchMetricsList = function () {
        commonService.apiGet("/metrics/metrics_list", "fetchMetricsList").then(function(metricsList) {
            $scope.metricsList = metricsList;
        });
    };

    $scope.selectedMetricChange = function (selectedMetric) {
        if($scope.selectedMetric) {
            commonService.apiGet("/metrics/describe_table/" + $scope.selectedMetric, "selectedMetricChange").then(function (currentTableFields) {
                $scope.currentTableFields = currentTableFields;
                let i = 0;
            });
        }

    };

    $scope.fetchChartList = (metricModelName) => {
        let payload = {};
        payload["metric_model_name"] = metricModelName;
        commonService.apiPost("/metrics/chart_list", payload, "fetchChartList").then((chartList) => {
        });
    };

    $scope.fetchChartsInfo = function (metricModelName) {
        let payload = {};
        payload["metric_model_name"] = metricModelName;
        commonService.apiPost("/metrics/charts_info", payload, "fetchChartsInfo").then((chartsInfo) => {
            $scope.chartsInfo = chartsInfo;

        });
    };

    $scope.fetchMetricsData = (metricModelName, chartName) => {
        let payload = {};
        payload["metric_model_name"] = metricModelName;
        payload["chart_name"] = chartName;
        commonService.apiPost("/metrics/data", payload, "fetchMetricsData").then((data) => {

        });
    }
}

angular.module('qa-dashboard').controller("metricsController", MetricsController);


