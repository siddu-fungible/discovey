'use strict';

function AnalyticsTablesController($scope, $http, commonService, $timeout) {
    let ctrl = this;

    ctrl.$onInit = function () {
    };

    ctrl.$postLink = function () {

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

    $scope.prepareKey = (valueList) => {
        let s = "";
        valueList.forEach((value) => {
            s += value;
        });
        return s;
    };

    $scope.fetchTableData = () => {
        let payload = {};
        payload["metric_model_name"] = $scope.metricModelName;
        payload["chart_name"] = $scope.chartName;
        commonService.apiPost("/metrics/table_data", payload, "fetchTableData").then((data) => {
            let remoteTable = data["data"];
            let headers = data["headers"];
            let uniqueKeys = data["unique_keys"];
            let processedTable = {};

            remoteTable.forEach((oneRemoteRow) => {
                let inputValueList = [];
                let rowOutput = {};
                let lastKey = null;
                headers.forEach((headerName) => {
                    if(headerName.startsWith("key")) {
                        lastKey = headerName;
                    }
                    if(headerName.startsWith("input")) {
                        inputValueList.push(oneRemoteRow[headerName]);
                    } else if(headerName.startsWith("output")) {
                        if(!headerName in rowOutput) {
                            rowOutput[headerName] = {};
                            uniqueKeys.forEach((uniqueKey) => {
                                rowOutput[headerName][uniqueKey] = null;
                            });
                        } else {
                            rowOutput[headerName][lastKey] = oneRemoteRow[headerName];
                        }
                    }

                });
                let preparedKey = $scope.prepareKey(inputValueList);
                if(!preparedKey in processedTable) {

                    processedTable[preparedKey] = {"inputs": inputValueList, "outputs": {}};
                }
                headers.forEach((headerName) => {
                    if(headerName.startsWith("ouput")) {
                       processedTable[preparedKey].outputs
                    }
                })

            });

            // Time to look at the outputs

            let o = 1;
        });
    };

    $scope.test = () => {
        console.log($scope.metricModelName);

    }

}



angular.module('qa-dashboard').controller("analyticsTablesController", AnalyticsTablesController);
