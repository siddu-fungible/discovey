'use strict';

function MetricsController($scope, $http, commonService, $timeout) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.metricsList = [];
        $scope.fetchMetricsList();
        $scope.currentTableFields = null;
        $scope.fetchChartList("Performance1");
        $scope.fetchChartsInfo("Performance1");
        /*$scope.fetchMetricsData("Performance1", "Chart 1");*/
        $scope.series = ["123", "143", 156];
        $scope.charting = true;


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
            angular.forEach($scope.chartsInfo, (chartInfo, chartName) => {
                $scope.fetchMetricsData(metricModelName, chartName, chartInfo);
            });

        });
    };

    $scope.fetchMetricsData = (metricModelName, chartName, chartInfo) => {
        $scope.title = chartName;
        let payload = {};
        payload["metric_model_name"] = metricModelName;
        payload["chart_name"] = chartName;
        commonService.apiPost("/metrics/data", payload, "fetchMetricsData").then((allDataSets) => {

            let keySet = new Set();
            let firstDataSet = allDataSets[0];
            firstDataSet.forEach((oneRecord) => {
                keySet.add(oneRecord.key.toString());
            });
            let keyList = Array.from(keySet);

            let chartDataSets = [];
            let dataSetIndex = 0;
            allDataSets.forEach((oneDataSet) => {

                let oneChartDataArray = [];
                for(let i = 0; i < keyList.length; i++) {
                    let output = null;
                    for(let j = 0; j < oneDataSet.length; j++) {
                        let oneRecord = oneDataSet[j];
                        if(oneRecord.key.toString() === keyList[i]) {
                            output = oneRecord[chartInfo.data_sets[0].output.name];
                            break;
                        }
                    }
                    oneChartDataArray.push(output);
                }
                let oneChartDataSet = {name: chartInfo.data_sets[dataSetIndex].name, data: oneChartDataArray};
                chartDataSets.push(oneChartDataSet);
                dataSetIndex++;
            });
            $scope.someValues = chartDataSets;


        });
    }
}

angular.module('qa-dashboard').controller("metricsController", MetricsController);


