'use strict';

function AnalyticsTablesController($scope, $http, commonService, $timeout) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.metricModelName = ctrl.modelName;
        $scope.chartName = ctrl.chartName;

        console.log($scope.metricModelName);
        console.log($scope.chartName);
        $scope.describeTable().then(() => {
            $scope.fetchTableData();
        });
        //$scope.fetchTableData();
    };

    $scope.describeTable = () => {
        $scope.inputs = [];
        $scope.outputList = [];
        return commonService.apiGet("/metrics/describe_table/" + $scope.metricModelName, "fetchMetricsData").then(function (tableInfo) {
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

    $scope.getVerboseName = (name) => {
        return $scope.tableInfo[name].verbose_name;
    };


    $scope.filterHeaders = (headers, input) => {
        if (!headers) {
            return;
        }
        return headers.filter((header) => {
            if(input === "input") {
                return header.startsWith("input");
            } else {
                return header.startsWith("output");
            }
        });
    };

    $scope.prepareKey = (valueList) => {
        let s = "";
        valueList.forEach((value) => {
            s += value;
        });
        return s;
    };

    $scope.getOutputHeaders = () => {
        let result = [];
        if($scope.headers) {
            let outputHeaders = $scope.filterHeaders($scope.headers, "output");
            if(outputHeaders.length > 0) {
                outputHeaders.forEach((outputHeader) => {
                    $scope.uniqueKeys.forEach((uniqueKey) => {
                        result.push(uniqueKey);
                    })
                });
            }

        }
        return result;
    };

    $scope.fetchTableData = () => {
        let payload = {};
        payload["metric_model_name"] = $scope.metricModelName;
        payload["chart_name"] = $scope.chartName;
        commonService.apiPost("/metrics/table_data", payload, "fetchTableData").then((data) => {
            let remoteTable = data["data"];
            $scope.headers = data["headers"];
            $scope.uniqueKeys = data["unique_keys"];
            $scope.processedRows = {};

            remoteTable.forEach((oneRemoteRow) => {
                let inputValueList = [];
                let rowOutput = {};
                let lastKey = null;
                $scope.headers.forEach((headerName) => {
                    if(headerName.startsWith("key")) {
                        lastKey = oneRemoteRow[headerName];
                    }
                    if(headerName.startsWith("input")) {
                        inputValueList.push(oneRemoteRow[headerName]);
                    } else if(headerName.startsWith("output")) {
                        if(!rowOutput.hasOwnProperty(headerName)) {
                            rowOutput[headerName] = {};
                            $scope.uniqueKeys.forEach((uniqueKey) => {
                                rowOutput[headerName][uniqueKey] = null;
                            });
                        } else {
                            rowOutput[headerName][lastKey] = oneRemoteRow[headerName];
                        }
                    }

                });
                let preparedKey = $scope.prepareKey(inputValueList);
                if(!$scope.processedRows.hasOwnProperty(preparedKey)) {

                    $scope.processedRows[preparedKey] = {"inputs": inputValueList, "outputs": {}};
                }
                $scope.headers.forEach((headerName) => {
                    if(headerName.startsWith("output")) {
                        if(!$scope.processedRows[preparedKey].outputs.hasOwnProperty(headerName)) {
                            $scope.processedRows[preparedKey].outputs[headerName] = {};
                        }
                        $scope.processedRows[preparedKey].outputs[headerName][lastKey] = oneRemoteRow[headerName];
                    }
                })

            });

            // Time to look at the outputs

            let o = 1;
            $scope.outputHeaders = $scope.getOutputHeaders();

        });
    };

    $scope.test = () => {
        console.log($scope.metricModelName);

    };

    $scope.getOutputValues = (rowKey) => {
        let justValues = [];
        $scope.filterHeaders($scope.headers, "output").forEach((outputHeader) => {
            $scope.uniqueKeys.forEach((key) => {
                let justOutputs = $scope.processedRows[rowKey].outputs;
                justValues.push(justOutputs[outputHeader][key]);
            });
        });
        return justValues;
    }

}


angular.module('qa-dashboard').component('analyticsTables', {
        templateUrl: '/static/qa_dashboard/analytics_tables_template.html',
        controller: AnalyticsTablesController,
        bindings: {
            modelName: '@',
            chartName: '@'
        }
});

