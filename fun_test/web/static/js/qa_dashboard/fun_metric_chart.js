'use strict';


function FunMetricChartController($scope, commonService) {

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
        /*$scope.pointClickCallback = ctrl.pointClickCallback;*/
    };

    $scope.pointClickCallback = (point) => {
        ctrl.pointClickCallback()(point);
    };

    $scope.xAxisFormatter = (value) => {
        return ctrl.xaxisFormatter()(value);
    };

    $scope.tooltipFormatter = (x, y) => {
        return ctrl.tooltipFormatter()(x, y);
    };

    $scope.$watch(function () {
        return ctrl.previewDataSets;
    }, function (newvalue, oldvalue) {
        if (newvalue === oldvalue) {
            console.log(newvalue, oldvalue);
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

    $scope.fetchMetricsData = (metricModelName, chartName, chartInfo, previewDataSets) => {
        $scope.title = chartName;
        if(!chartName) {
            return;
        }

        commonService.apiGet("/metrics/describe_table/" + metricModelName, "fetchMetricsData").then(function (tableInfo) {
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
                allDataSets.forEach((oneDataSet) => {

                    let oneChartDataArray = [];
                    for(let i = 0; i < keyList.length; i++) {
                        let output = null;
                        for(let j = 0; j < oneDataSet.length; j++) {
                            let oneRecord = oneDataSet[j];
                            if(oneRecord.key.toString() === keyList[i]) {
                                let outputName = filterDataSets[0].output.name;
                                output = oneRecord[outputName];
                                $scope.chart1YaxisTitle = tableInfo[outputName].verbose_name;
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
        template: '<fun-chart values="values" series="series"\n' +
        '                   title="$ctrl.chartName" charting="charting" chart-type="line-chart"\n' +
        '                   width="width" height="height" xaxis-title="chart1XaxisTitle" yaxis-title="chart1YaxisTitle"\n' +
        '                   point-click-callback="pointClickCallback" xaxis-formatter="xAxisFormatter"\n' +
        '                   tooltip-formatter="tooltipFormatter">\n' +
        '                   \n' +
        '        </fun-chart>',

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
        controller: FunMetricChartController
 });