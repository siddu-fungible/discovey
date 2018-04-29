'use strict';


function FunMetricChartController($scope, commonService, $attrs) {

    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        if(ctrl.chartName) {
            $scope.fetchChartInfo();
        }

        $scope.values = null;
        $scope.charting = true;
        //console.log(ctrl.width);
        $scope.width = ctrl.width;
        $scope.height = ctrl.height;
        $scope.pointClickCallback = null;
        $scope.xAxisFormatter = null;
        $scope.tooltipFormatter = null;
        if (ctrl.pointClickCallback) {
            $scope.pointClickCallback = (point) => {
                if(!$attrs.pointClickCallback) return null;
                ctrl.pointClickCallback()(point);
            };
        }

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
        console.log(ctrl.showingTable);
        /*$scope.pointClickCallback = ctrl.pointClickCallback;*/
    };

    $scope.cleanValue = (key, value) => {
        if (key === "key" && (ctrl.xaxisFormatter)) {
            return ctrl.xaxisFormatter()(value);
        } else {
            return value;
        }
    };


    $scope.$watch(function () {
        return ctrl.previewDataSets;
    }, function (newvalue, oldvalue) {
        if (newvalue === oldvalue) {
            // console.log(newvalue, oldvalue);
            return;
        }
        // let i = 0;
        // console.log(newvalue, oldvalue);
        if($scope.chartInfo) {
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, $scope.chartInfo, ctrl.previewDataSets); // TODO: Race condition on chartInfo
        } else {
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, null, ctrl.previewDataSets); // TODO: Race condition on chartInfo
        }

    }, true);

    $scope.fetchChartInfo = () => {
        let payload = {};
        payload["metric_model_name"] = ctrl.modelName;
        payload["chart_name"] = ctrl.chartName;
        // Fetch chart info
        commonService.apiPost("/metrics/chart_info", payload, "fun_metric_chart: chart_info").then((chartInfo) => {
            $scope.chartInfo = chartInfo;
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, chartInfo, null)
        })
    };

    $scope.getValidatedData = (data, minimum, maximum) => {
        let result = data;
        result = {
            y: data,
            marker: {
                radius: 3
            },
        };
        if(data < minimum || data > maximum) {
            result =
                {
                    y: data,
                    marker: {
                        symbol: 'cross',
                        lineColor: 'red',
                        lineWidth: 5
                    }
                }
        }
        return result;
    };

    $scope.hideTable = () => {
        $scope.showingTable = false;
    };

    $scope.showTable = () => {
        $scope.showingTable = true;
    };

    $scope.fetchMetricsData = (metricModelName, chartName, chartInfo, previewDataSets) => {
        $scope.title = chartName;
        if(!chartName) {
            return;
        }

        commonService.apiGet("/metrics/describe_table/" + metricModelName, "fetchMetricsData").then(function (tableInfo) {
            $scope.tableInfo = tableInfo;
            let payload = {};
            payload["metric_model_name"] = metricModelName;
            payload["chart_name"] = chartName;
            payload["preview_data_sets"] = previewDataSets;
            let filterDataSets = [];
            if(previewDataSets) {
                filterDataSets = previewDataSets;
            } else {
                if(chartInfo){
                    filterDataSets = chartInfo.data_sets;
                }
            }
            $scope.filterDataSets = filterDataSets;

            commonService.apiPost("/metrics/data", payload, "fetchMetricsData").then((allDataSets) => {
                if(allDataSets.length === 0) {
                    $scope.values = null;
                    return;
                }

                let keySet = new Set();
                let firstDataSet = allDataSets[0];
                firstDataSet.forEach((oneRecord) => {
                    keySet.add(oneRecord.key.toString());
                });
                let keyList = Array.from(keySet);
                keyList.sort();
                $scope.series = keyList;

                let chartDataSets = [];
                let dataSetIndex = 0;
                $scope.allData = allDataSets;
                allDataSets.forEach((oneDataSet) => {

                    let oneChartDataArray = [];
                    for(let i = 0; i < keyList.length; i++) {
                        let output = null;
                        for(let j = 0; j < oneDataSet.length; j++) {
                            let oneRecord = oneDataSet[j];
                            if(oneRecord.key.toString() === keyList[i]) {
                                let outputName = filterDataSets[dataSetIndex].output.name;
                                output = oneRecord[outputName];
                                if (chartInfo && chartInfo.y1axis_title) {
                                   $scope.chart1YaxisTitle = chartInfo.y1axis_title;
                                } else {
                                   $scope.chart1YaxisTitle = tableInfo[outputName].verbose_name;
                                }
                                if (ctrl.y1AxisTitle) {
                                    $scope.chart1YaxisTitle = ctrl.y1AxisTitle;
                                }


                                $scope.chart1XaxisTitle = tableInfo["key"].verbose_name;
                                break;
                            }
                        }
                        let thisMinimum = filterDataSets[dataSetIndex].output.min;
                        let thisMaximum = filterDataSets[dataSetIndex].output.max;

                        oneChartDataArray.push($scope.getValidatedData(output, thisMinimum, thisMaximum));
                    }
                    let oneChartDataSet = {name: filterDataSets[dataSetIndex].name, data: oneChartDataArray};
                    chartDataSets.push(oneChartDataSet);
                    dataSetIndex++;
                });
                $scope.values = chartDataSets;
            });
        });
    }
}

angular.module('qa-dashboard').component("funMetricChart", {
        templateUrl: '/static/qa_dashboard/fun_metric_chart.html',
        bindings: {
                    chartName: '<',
                    y1AxisTitle: '<',
                    modelName: '<',
                    width: '@',
                    height: '@',
                    previewDataSets: '<',
                    pointClickCallback: '&',
                    xaxisFormatter: '&',
                    tooltipFormatter: '&',
                    showingTable: '<'
                  },
        controller: FunMetricChartController
 });