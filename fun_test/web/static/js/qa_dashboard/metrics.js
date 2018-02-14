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

    $scope.addChartClick = (modelName) => {
        $modal.open({
            templateUrl: "/static/qa_dashboard/edit_chart.html",
            controller: ['$modalInstance', '$scope', 'commonService', '$http', 'chartName', 'modelName', EditChartController],
            resolve: {
                chartName: () => {
                    return null;
                },
                modelName: () => {
                    return modelName;
                }
            }
        }).result.then(function () {
        }).catch(function () {
        });
    };

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
        }).catch(function () {
        });
    };

    function EditChartController($modalInstance, $scope, commonService, $http, chartName, modelName) {
        let ctrl = this;
        $scope.mode = "Edit";
        if(!chartName) {
            $scope.mode = "Create";
        }
        $scope.chartName = chartName;
        $scope.modelName = modelName;
        $scope.chartInfo = null;
        $scope.copyChartInfo = null;
        $scope.previewDataSets = [];
        $scope.addDataSet = null;
        $scope.outputList = [];
        $scope.tableInfo = null;
        $scope.dummyChartInfo = {"output": {"min": 0, "max": "99999"}};

        let payload = {};
        payload["metric_model_name"] = modelName;
        payload["chart_name"] = chartName;

        $scope.describeTable = () => {
            $scope.inputs = [];
            commonService.apiGet("/metrics/describe_table/" + modelName, "fetchMetricsData").then(function (tableInfo) {
                $scope.tableInfo = tableInfo;
                angular.forEach($scope.tableInfo, (fieldInfo, field) => {
                    let oneField = {};
                    oneField.name = field;
                    if('choices' in fieldInfo && oneField.name.startsWith("input")) {
                        oneField.choices = fieldInfo.choices.map((choice)=> { return choice[1]});
                        $scope.inputs.push(oneField);
                    }
                    if(oneField.name.startsWith("output")) {
                        $scope.outputList.push(oneField.name);
                    }
                });
            });
        };

        $scope.outputChange = () => {
            if($scope.selectedOutput) {
                $scope.dummyChartInfo.output.name = $scope.selectedOutput;
            }
        };


        $scope.describeTable();

        // Fetch chart info


        if($scope.chartName) {
            commonService.apiPost("/metrics/chart_info", payload, "EditChartController: chart_info").then((chartInfo) => {
                $scope.chartInfo = chartInfo;
                //$scope.copyChartInfo = angular.copy($scope.chartInfo);
                $scope.previewDataSets = $scope.chartInfo.data_sets;
            });
        } else {
        }


        $scope.addDataSetClick = () => {
            //let newDataSet = {};

            if(!$scope.tableInfo) {
                return $scope.describeTable();
            }
            $scope.addDataSet = {};



            $scope.addDataSet["inputs"] = $scope.inputs;
            let outputName = "";
            if($scope.previewDataSets.length > 0) {
                let firstChartInfoDataSet = $scope.previewDataSets.data_sets[0];
                outputName = firstChartInfoDataSet.output.name;
                $scope.selectedOutput = outputName;
            } else {
                outputName = $scope.selectedOutput;
            }

            $scope.addDataSet["output"] = {"name": $scope.selectedOutput, "min": 0, "max": 99999};

            /*newDataSet["inputs"] = {};
            $scope.addDataSet["inputs"].forEach((oneField) => {
                newDataSet["inputs"][oneField.name] = oneField.selectedChoice;
            })*/

        };

        $scope.addClick = () => {
            //
            let validDataSet = {};
            validDataSet["inputs"] = {};
            validDataSet["output"] = {};
            if($scope.addDataSet) {
                // lets validate all inputs
                $scope.addDataSet["inputs"].forEach((oneField) => {
                    if(!oneField.selectedChoice) {
                        let message = "Please select a choice for " + oneField.name;
                        alert(message);
                        return commonService.showError(message);
                    } else {
                        validDataSet["inputs"][oneField.name] = oneField.selectedChoice;

                    }
                });
                if(!$scope.addDataSet.name) {
                    let message = "Please provide a name for the data-set";
                    alert(message);
                    return commonService.showError(message);
                } else {
                    validDataSet["name"] = $scope.addDataSet.name;
                    validDataSet["output"]["name"] = $scope.addDataSet["output"].name;
                    validDataSet["output"]["min"] = $scope.addDataSet["output"].min;
                    validDataSet["output"]["max"] = $scope.addDataSet["output"].max;
                }
            }

            $scope.previewDataSets.push(validDataSet);
            $scope.addDataSet = null;

        };


        $scope.removeClick = (index) => {
            //$scope.copyChartInfo.data_sets.splice(index, 1);
            $scope.previewDataSets.splice(index, 1);
                //= $scope.copyChartInfo.data_sets;
        };

        $scope.submit = () => {
            //$scope.previewDataSets = $scope.copyChartInfo.data_sets;
            let payload = {};
            payload["metric_model_name"] = $scope.modelName;
            payload["chart_name"] = $scope.chartName;
            payload["data_sets"] = $scope.previewDataSets;
            commonService.apiPost('/metrics/update_chart', payload, "EditChart: Submit").then((data) => {
                if(data) {
                    alert("Submitted");
                }
            });
        }
    }
}



angular.module('qa-dashboard').controller("metricsController", MetricsController);


