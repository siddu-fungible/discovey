'use strict';

function MetricsController($scope, $http, commonService, $timeout, $modal) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.metricsList = [];
        $scope.fetchModules();
        $scope.modelsInfo = {};

    };

    $scope.moduleChange = () => {
        console.log($scope.selectedModule);
        let payload = {};
        let thisModule = $scope.selectedModule;
        if ($scope.selectedModule) {
            payload["module_name"] = $scope.selectedModule;
            /*
            commonService.apiPost("/metrics/charts_by_module", payload, "fetchModules get charts by module").then((charts) => {

                $scope.chartInfos[thisModule] = charts;
                let i = 0;
            })*/

            commonService.apiPost("/metrics/models_by_module", payload, "moduleChange").then((models) => {
                $scope.modelsInfo[thisModule] = models;
            })
        }

    };

    $scope.fetchModules = () => {
        commonService.apiGet("/regression/modules", "fetchModules").then((modules) => {
            $scope.modules = modules;
            $scope.modules.forEach((module) => {
                let moduleName = module.name;
                // Get charts by module

            })
        })
    };

    /*

    $scope.fetchMetricsList = function () {
        commonService.apiGet("/metrics/metrics_list", "fetchMetricsList").then(function (metricsList) {
            $scope.metricsList = metricsList;
        });
    };

    $scope.selectedMetricChange = function (selectedMetric) {
        if ($scope.selectedMetric) {
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
    */

    $scope.editChartClick = (chartName, modelName) => {
        $modal.open({
            templateUrl: "/static/qa_dashboard/edit_chart.html",
            controller: ['$modalInstance', '$scope', 'commonService', '$http', 'chartName', 'modelName', EditChartController],
            resolve: {
                chartName: () => {
                    return chartName;
                },
                modelName: () => {
                    return modelName;
                }
            }
        }).result.then(function () {
        })


    };

    function EditChartController($modalInstance, $scope, commonService, $http, chartName, modelName) {
        let ctrl = this;
        $scope.chartName = chartName;
        $scope.modelName = modelName;
        $scope.chartInfo = null;
        $scope.copyChartInfo = null;
        $scope.previewDataSets = null;

        let payload = {};
        payload["metric_model_name"] = modelName;
        payload["chart_name"] = chartName;
        // Fetch chart info

        commonService.apiPost("/metrics/chart_info", payload, "EditChartController: chart_info").then((chartInfo) => {
            $scope.chartInfo = chartInfo;
            $scope.copyChartInfo = angular.copy($scope.chartInfo);
            let i = 0;
        });

        $scope.removeClick = (index) => {
            $scope.copyChartInfo.data_sets.splice(index, 1);
            let i = 0;
            $scope.previewDataSets = $scope.copyChartInfo.data_sets;
        };

        $scope.submit = () => {
            let i = 0;
            $scope.previewDataSets = $scope.copyChartInfo.data_sets;

        }
    }
}



angular.module('qa-dashboard').controller("metricsController", MetricsController);


