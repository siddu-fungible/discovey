'use strict';


function FunMetricChartController($scope, commonService) {

    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.fetchChartInfo();
        $scope.values = null;
        $scope.charting = true;
        //console.log(ctrl.width);
        $scope.width = ctrl.width;
        $scope.height = ctrl.height;
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
        $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, $scope.chartInfo, ctrl.previewDataSets); // TODO: Race condition on chartInfo
    }, true);

    $scope.fetchChartInfo = () => {
        let payload = {};
        payload["metric_model_name"] = ctrl.modelName;
        payload["chart_name"] = ctrl.chartName;
        // Fetch chart info
        commonService.apiPost("/metrics/chart_info", payload, "EditChartController: chart_info").then((chartInfo) => {
            $scope.chartInfo = chartInfo;
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, chartInfo, null)
        })
    };

    $scope.getValidatedData = (data, minimum, maximum) => {
        let result = data;
        if(data < minimum || data > maximum) {
            result =
                {
                    y: data,
                    marker: {
                        symbol: 'cross',
                        lineColor: 'red',
                        lineWidth: 4
                    }
                }
        }
        return result;
    };

    $scope.fetchMetricsData = (metricModelName, chartName, chartInfo, previewDataSets) => {
        $scope.title = chartName;

        commonService.apiGet("/metrics/describe_table/" + metricModelName, "fetchMetricsData").then(function (tableInfo) {
            let payload = {};
            payload["metric_model_name"] = metricModelName;
            payload["chart_name"] = chartName;
            payload["preview_data_sets"] = previewDataSets;

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
                                let outputName = chartInfo.data_sets[0].output.name;
                                output = oneRecord[outputName];
                                $scope.chart1YaxisTitle = tableInfo[outputName].verbose_name;
                                $scope.chart1XaxisTitle = tableInfo["key"].verbose_name;
                                break;
                            }
                        }
                        let thisMinimum = chartInfo.data_sets[dataSetIndex].output.min;
                        let thisMaximum = chartInfo.data_sets[dataSetIndex].output.max;

                        oneChartDataArray.push($scope.getValidatedData(output, thisMinimum, thisMaximum));
                    }
                    let oneChartDataSet = {name: chartInfo.data_sets[dataSetIndex].name, data: oneChartDataArray};
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
        '                   width="width" height="height" xaxis-title="chart1XaxisTitle" yaxis-title="chart1YaxisTitle">\n' +
        '                   \n' +
        '        </fun-chart>',

        bindings: {
                    chartName: '<',
                    modelName: '<',
                    width: '@',
                    height: '@',
                    previewDataSets: '<'
                  },
        controller: FunMetricChartController
 });