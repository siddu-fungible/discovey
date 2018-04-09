'use strict';


function EditableMetricChartController($scope, commonService, $attrs) {
    let ctrl = this;

    ctrl.$onInit = () => {
        $scope.editing = false;
        $scope.chartName = ctrl.chartName;
        $scope.modelName = ctrl.modelName;
        $scope.chartInfo = null;
        $scope.copyChartInfo = null;
        $scope.previewDataSets = [];
        $scope.addDataSet = null;
        $scope.outputList = [];
        $scope.tableInfo = null;
        $scope.dummyChartInfo = {"output": {"min": 0, "max": "99999"}};
        $scope.showOutputSelection = true;
        $scope.negativeGradient = null;

        if (ctrl.xaxisFormatter) {
            $scope.xAxisFormatter = (value) => {
                if(!$attrs.xaxisFormatter) return null;
                return ctrl.xaxisFormatter()(value);
            };
        }

        if (ctrl.tooltipFormatter) {
            $scope.tooltipFormatter = (x, y) => {
                if(!$attrs.tooltipFormatter) return null;
                return ctrl.tooltipFormatter()(x, y);
            };
        }


        $scope.describeTable().then(function() {
            $scope.fetchChartInfo();
        });

        $scope.currentDescription = "---";
    };

    $scope.$watch(function () {
        return ctrl.chartName;
    }, function (newvalue, oldvalue) {
        if (newvalue === oldvalue) {
            console.log(newvalue, oldvalue);
        }
        ctrl.$onInit();
    });

    $scope.editClick = () => {
        $scope.editing = true;
    };

    $scope.dismiss = () => {
        $scope.editing = false;
    };


    $scope.describeTable = () => {

        $scope.inputs = [];
        return commonService.apiGet("/metrics/describe_table/" + ctrl.modelName, "fetchMetricsData").then(function (tableInfo) {
            $scope.tableInfo = tableInfo;
            angular.forEach($scope.tableInfo, (fieldInfo, field) => {
                let oneField = {};
                oneField.name = field;
                if ('choices' in fieldInfo && oneField.name.startsWith("input")) {
                    oneField.choices = fieldInfo.choices.map((choice) => {
                        return choice[1]
                    });
                    $scope.inputs.push(oneField);
                }
                if (oneField.name.startsWith("output")) {
                    $scope.outputList.push(oneField.name);
                }
            });
        });

    };

    $scope.outputChange = () => {
        if ($scope.selectedOutput) {
            $scope.dummyChartInfo.output.name = $scope.selectedOutput;
        }
    };



    $scope.fetchChartInfo = () => {
        // Fetch chart info
        let payload = {};
        payload["metric_model_name"] = ctrl.modelName;
        payload["chart_name"] = ctrl.chartName;
        if ($scope.chartName) {
            commonService.apiPost("/metrics/chart_info", payload, "EditableMetricChartController: chart_info").then((chartInfo) => {
                $scope.chartInfo = chartInfo;
                //$scope.copyChartInfo = angular.copy($scope.chartInfo);
                $scope.previewDataSets = $scope.chartInfo.data_sets;
                $scope.currentDescription = $scope.chartInfo.description;
            });
        } else {

        }
    };




    $scope.addDataSetClick = () => {
        //let newDataSet = {};

        if (!$scope.tableInfo) {
            return $scope.describeTable();
        }
        $scope.addDataSet = {};


        $scope.addDataSet["inputs"] = $scope.inputs;
        let outputName = "";
        if ($scope.previewDataSets.length > 0) {
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
        $scope.showOutputSelection = false;

        //
        let validDataSet = {};
        validDataSet["inputs"] = {};
        validDataSet["output"] = {};
        if ($scope.addDataSet) {
            // lets validate all inputs
            $scope.addDataSet["inputs"].forEach((oneField) => {
                if (!oneField.selectedChoice) {
                    let message = "Please select a choice for " + oneField.name;
                    alert(message);
                    return commonService.showError(message);
                } else {
                    validDataSet["inputs"][oneField.name] = oneField.selectedChoice;

                }
            });
            if (!$scope.addDataSet.name) {
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
        payload["description"] = $scope.currentDescription;
        payload["negative_gradient"] = $scope.negativeGradient;
        commonService.apiPost('/metrics/update_chart', payload, "EditChart: Submit").then((data) => {
            if (data) {
                alert("Submitted");
                $scope.dismiss();
            } else {
                alert("Submission failed. Please check alerts");
            }

        });
    }
}

angular.module('qa-dashboard').component("editableMetricChart", {
    templateUrl: '/static/qa_dashboard/editable_metric_chart.html',

    bindings: {
        chartName: '<',
        modelName: '<',
        width: '@',
        height: '@',
        previewDataSets: '<',
        pointClickCallback: '&',
        xaxisFormatter: '&',
        tooltipFormatter: '&'
    },
    controller: EditableMetricChartController
});
