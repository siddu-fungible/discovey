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
        //console.log(ctrl.showingTable);
        /*$scope.pointClickCallback = ctrl.pointClickCallback;*/
    };

    $scope.cleanValue = (key, value) => {
        try {
            if (key === "input_date_time" && (ctrl.xaxisFormatter) && ctrl.xaxisFormatter()()) {
                return ctrl.xaxisFormatter()(value);
            } else {
                return value;
            }
        } catch (e) {

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
        //$scope.status = "Fetching chart info";
        commonService.apiPost("/metrics/chart_info", payload, "fun_metric_chart: chart_info").then((chartInfo) => {
            $scope.chartInfo = chartInfo;
            $scope.status = "idle";
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

        /*
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
        }*/


        return result;
    };

    $scope.hideTable = () => {
        $scope.showingTable = false;
    };

    $scope.showTable = () => {
        $scope.showingTable = true;
    };

    $scope.shortenKeyList = (keyList) => {
        let newList = [];
        keyList.forEach((key) => {
            let r = /(\d{4})-(\d{2})-(\d{2})/g;
            let match = r.exec(key);
            let s = match[2] + "/" + match[3];
            newList.push(s)
        });
        return newList;
    };

    $scope.isFieldRelevant = (fieldName) => {
        let relevant = false;
        if (fieldName === "input_date_time") {
            relevant = true;
        }
        $scope.filterDataSets.forEach((oneDataSet) => {
            angular.forEach(oneDataSet.inputs, (value, key) => {
                if (key === fieldName) {
                    relevant = true;
                }
            });
            if (fieldName === oneDataSet.output.name) {
                relevant = true;
            }
        });
        return relevant;
    };


    function sameDay(d1, d2) {
          return d1.getFullYear() === d2.getUTCFullYear() &&
            d1.getUTCMonth() === d2.getUTCMonth() &&
            d1.getUTCDate() === d2.getUTCDate();
    }

    $scope.fixMissingDates = (dates) => {
        let firstDate = new Date(dates[0].replace(/\s+/g, 'T'));
        let today = new Date();
        let yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        let lastDate = yesterday;

        let currentDate = firstDate;
        let datesIndex = 0;
        let finalDates = [];
        while (currentDate <= yesterday) {

            //console.log(currentDate);
            if ((datesIndex < dates.length) && sameDay(new Date(dates[datesIndex].replace(/\s+/g, 'T')), currentDate)) {
                finalDates.push(dates[datesIndex]);
                datesIndex++;
                while ((datesIndex < dates.length) && sameDay(new Date(dates[datesIndex].replace(/\s+/g, 'T')), currentDate)) {
                    finalDates.push(dates[datesIndex]);
                    datesIndex++;
                }
            } else {
                finalDates.push(currentDate.toISOString().replace("T", " "));  // TODO: convert zone correctly
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }
        let j = 0;
        return finalDates;
    };

    $scope.fetchMetricsData = (metricModelName, chartName, chartInfo, previewDataSets) => {
        $scope.title = chartName;
        if(!chartName) {
            return;
        }
        //$scope.status = "Fetch table meta-data";
        commonService.apiGet("/metrics/describe_table/" + metricModelName, "fetchMetricsData").then(function (tableInfo) {
            $scope.status = "idle";
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

            $scope.status = "Fetch data";
            commonService.apiPost("/metrics/data", payload, "fetchMetricsData").then((allDataSets) => {
                $scope.status = "idle";
                if(allDataSets.length === 0) {
                    $scope.values = null;
                    return;
                }

                let keySet = new Set();
                /*
                let firstDataSet = allDataSets[0];
                firstDataSet.forEach((oneRecord) => {
                    keySet.add(oneRecord.input_date_time.toString());
                });*/
                allDataSets.forEach((oneDataSet) => {
                    oneDataSet.forEach((oneRecord) => {
                        keySet.add(oneRecord.input_date_time.toString());
                    });
                });

                let keyList = Array.from(keySet);
                keyList.sort();
                $scope.shortenKeyList(keyList);
                keyList = $scope.fixMissingDates(keyList);
                $scope.series = keyList;


                let chartDataSets = [];
                let dataSetIndex = 0;

                /*
                $scope.allData = allDataSets;
                $scope.status = "Preparing chart data-sets";
                allDataSets.forEach((oneDataSet) => {

                    let oneChartDataArray = [];
                    for(let i = 0; i < keyList.length; i++) {
                        let output = null;
                        for(let j = 0; j < oneDataSet.length; j++) {
                            let oneRecord = oneDataSet[j];
                            if(oneRecord.input_date_time.toString() === keyList[i]) {
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


                                $scope.chart1XaxisTitle = tableInfo["input_date_time"].verbose_name;
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

                */

                $scope.allData = allDataSets;
                $scope.status = "Preparing chart data-sets";
                allDataSets.forEach((oneDataSet) => {

                    let oneChartDataArray = [];
                    for(let i = 0; i < keyList.length; i++) {
                        let output = null;


                        let matchingDateFound = false;
                        for(let j = 0; j < oneDataSet.length; j++) {
                            let oneRecord = oneDataSet[j];
                            if(oneRecord.input_date_time.toString() === keyList[i]) {
                                matchingDateFound = true;
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


                                $scope.chart1XaxisTitle = tableInfo["input_date_time"].verbose_name;
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



                $scope.status = "idle";
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