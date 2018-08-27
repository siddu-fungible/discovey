'use strict';


function FunMetricChartController($scope, commonService, $attrs, $q, $timeout) {

    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.setDefault();
        $scope.chartInfo = ctrl.chartInfo;
        //console.log("OnInit: CI:" + $scope.chartInfo);
        $scope.waitTime = 0;
        if (ctrl.waitTime) {
            $scope.waitTime = parseInt(ctrl.waitTime);
            //console.log("My wait:" + $scope.waitTime);
        }

        if (ctrl.chartName) {
            $scope.fetchChartInfo().then((chartInfo) => {
                let thisChartInfo = chartInfo;
                $timeout(() => {
                    $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, thisChartInfo, null);
                }, $scope.waitTime);
            })
        }

        $scope.values = null;
        $scope.charting = true;
        //console.log(ctrl.width);
        $scope.width = ctrl.width;
        $scope.height = ctrl.height;
        $scope.pointClickCallback = null;
        $scope.xAxisFormatter = null;
        $scope.tooltipFormatter = null;
        $scope.tableInfo = ctrl.tableInfo;
        if (ctrl.pointClickCallback) {
            $scope.pointClickCallback = (point) => {
                if (!$attrs.pointClickCallback) return null;
                ctrl.pointClickCallback()(point);
            };
        }

        if (ctrl.xaxisFormatter) {
            $scope.xAxisFormatter = (value) => {
                if (!$attrs.xaxisFormatter) {
                    return null;
                }
                else {
                    let s = "Error";
                    const monthNames = ["null", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                    let r = /(\d{4})-(\d{2})-(\d{2})/g;
                    let match = r.exec(value);

                    if ($scope.timeMode === "month") {
                        if (match) {
                            let month = parseInt(match[2]);
                            s = monthNames[month];
                        }
                    }
                    else {
                        if (match) {
                            s = match[2] + "/" + match[3];
                        }
                    }
                    return s;
                }

            };
        }

        if (ctrl.tooltipFormatter) {
            $scope.tooltipFormatter = (x, y) => {
                if (!$attrs.tooltipFormatter) return null;
                return ctrl.tooltipFormatter()(x, y);
            };
        }
        //console.log(ctrl.showingTable);
        /*$scope.pointClickCallback = ctrl.pointClickCallback;*/

    };

    $scope.cleanValue = (key, value) => {
        try {
            if (key === "input_date_time") {
                //return ctrl.xaxisFormatter()(value);
                let s = "Error";
                let r = /(\d{4})-(\d{2})-(\d{2})/g;
                let match = r.exec(value);
                if (match) {
                    s = match[2] + "/" + match[3];
                }
                return s;
            } else {
                return value;
            }
        } catch (e) {

        }

    };

    $scope.$watch(
        () => {
            return [ctrl.previewDataSets, ctrl.chartName];
        }, function (newvalue, oldvalue) {
            if (newvalue === oldvalue) {
                // console.log(newvalue, oldvalue);
                return;
            }
            $scope.setDefault();
            $scope.chartInfo = ctrl.chartInfo;
            $scope.fetchChartInfo().then(() => {
                //$scope.tableInfo = ctrl.tableInfo;
                //$scope.timeMode = ctrl.timeMode;
                //console.log("C I:" + ctrl.chartInfo);
                if($scope.chartInfo) {
                    $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, $scope.chartInfo, ctrl.previewDataSets); // TODO: Race condition on chartInfo
                } else {
                    $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, null, ctrl.previewDataSets); // TODO: Race condition on chartInfo
                }

            });

    }, true);

    $scope.setDefault = () => {
        $scope.timeMode = "all";
    };

    $scope.fetchChartInfo = () => {
        let payload = {};
        payload["metric_model_name"] = ctrl.modelName;
        payload["chart_name"] = ctrl.chartName;
        // Fetch chart info
        //$scope.status = "Fetching chart info";
        if (!$scope.chartInfo) {
            //console.log("Fetching CI already");
            return commonService.apiPost("/metrics/chart_info", payload, "fun_metric_chart: chart_info").then((chartInfo) => {
                $scope.chartInfo = chartInfo;
                $scope.status = "idle";
                return $scope.chartInfo;
            })
        } else {
            return $q.resolve($scope.chartInfo);
        }

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
          return d1.getFullYear() === d2.getFullYear() &&
            d1.getMonth() === d2.getMonth() &&
            d1.getDate() === d2.getDate();
    }

    $scope.fixMissingDates = (dates) => {
        let firstString = dates[0].replace(/\s+/g, 'T');
        //firstString = firstString.replace('+', 'Z');
        //firstString = firstString.substring(0, firstString.indexOf('Z'));
        let firstDate = new Date(firstString);
        let today = new Date();
        let yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        yesterday.setHours(23, 59, 59);
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
                    //finalDates.push(dates[datesIndex]);
                    datesIndex++;
                }
            } else {
                //currentDate.setHours(currentDate.getHours() - currentDate.getTimezoneOffset() / 60);
                let tempDate = currentDate;
                tempDate.setHours(0);
                tempDate.setMinutes(0);
                tempDate.setSeconds(1);
                tempDate = new Date(tempDate.getTime() - (tempDate.getTimezoneOffset() * 60000));
                finalDates.push(tempDate.toISOString().replace('T', ' ')); //TODO: convert zone correctly
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }
        let j = 0;
        return finalDates;
    };


    $scope.describeTable = (metricModelName) => {
        if (!$scope.tableInfo && metricModelName !== 'MetricContainer') {
            return commonService.apiGet("/metrics/describe_table/" + metricModelName, "fetchMetricsData").then(function (tableInfo) {
                //console.log("FunMetric: Describe table: " + metricModelName);
                $scope.tableInfo = tableInfo;
                return $scope.tableInfo;
            })
        } else {
            return $q.resolve($scope.tableInfo)
        }
    };

    $scope.getDatesByTimeModeForLeaf = (dateList) => {
        let len = dateList.length;
        let filteredDate = [];
        let result = [[len, 0]];
        if($scope.timeMode === "week") {
            for(let i = len - 1; i >= 0; i = i - 7)
            {
                if(i >= 7)
                {
                    filteredDate.push([i, i - 7 + 1]);
                }
                else {
                    filteredDate.push([i, 0]);
                }
            }
            result = filteredDate.reverse();
        }
        else if($scope.timeMode === "month") {
            let i = len - 1;
            let monthDays = {0: 31, 1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30};
            // how many days to decrement for each month depending on the number of days of the previous month
            while(i >= 0)
            {
                let latestDate = new Date(dateList[i].replace(/\s+/g, 'T'));
                let diff = i - monthDays[latestDate.getMonth()];
                if(diff >= 0)
                {
                    filteredDate.push([i, diff + 1]);
                }
                else {
                    filteredDate.push([i, 0]);
                }
                i = diff;
            }
            result = filteredDate.reverse();
        }
        else {
            for(let i = len - 1; i >= 0; i--)
            {
                filteredDate.push([i, i]);
            }
            result = filteredDate.reverse();
        }
        return result;
    };

    $scope.getDatesByTimeModeForContainers = (dateList) => {
        let len = dateList.length;
        let filteredDate = [];
        let result = dateList;
        if($scope.timeMode === "week") {
            for(let i = len - 1; i >= 0; i = i - 7)
            {
                filteredDate.push(dateList[i]);
            }
            result = filteredDate.reverse();
        }
        else if($scope.timeMode === "month") {
            let i = len - 1;
            let monthDays = {0: 31, 1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30};
            // how many days to decrement for each month depending on the number of days of the previous month
            while(i >= 0)
            {
                let latestDate = new Date(dateList[i].replace(/\s+/g, 'T'));
                filteredDate.push(dateList[i]);
                i = i - monthDays[latestDate.getMonth()];
            }
            result = filteredDate.reverse();
        }
        return result;
    };

    $scope.setTimeMode = (mode) => {
        $scope.timeMode = mode;
        if($scope.chartInfo) {
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, $scope.chartInfo, ctrl.previewDataSets); // TODO: Race condition on chartInfo
        } else {
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, null, ctrl.previewDataSets); // TODO: Race condition on chartInfo
        }
    };

    $scope.fetchMetricsData = (metricModelName, chartName, chartInfo, previewDataSets) => {
        $scope.title = chartName;
        if(!chartName) {
            return;
        }
        //$scope.status = "Fetch table meta-data";
        $scope.describeTable(metricModelName).then(function (tableInfo) {
            let payload = {};
            payload["metric_model_name"] = metricModelName;
            payload["chart_name"] = chartName;
            payload["preview_data_sets"] = previewDataSets;
            payload["metric_id"] = chartInfo["metric_id"];
            if(metricModelName !== 'MetricContainer') {
            $scope.status = "idle";
            $scope.tableInfo = tableInfo;

            let filterDataSets = [];
            if(previewDataSets) {
                filterDataSets = previewDataSets;
            } else {
                //console.log("Chart Info:" + chartInfo);
                if(chartInfo){
                    filterDataSets = chartInfo.data_sets;
                    //console.log("C DS:" + chartInfo.data_sets);
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
                let originalKeyList = keyList;
                keyList = $scope.getDatesByTimeModeForLeaf(keyList);

                let chartDataSets = [];
                let seriesDates = [];
                let dataSetIndex = 0;

                $scope.allData = allDataSets;
                $scope.status = "Preparing chart data-sets";
                allDataSets.forEach((oneDataSet) => {

                    let oneChartDataArray = [];
                    for(let i = 0; i < keyList.length; i++) {
                        let output = null;
                        let matchingDateFound = false;
                        seriesDates.push(originalKeyList[keyList[i][0]]);
                        let  startIndex = keyList[i][0];
                        let endIndex = keyList[i][1];
                        while(startIndex >= endIndex)
                        {
                            for(let j = 0; j < oneDataSet.length; j++) {
                                let oneRecord = oneDataSet[j];
                                if (oneRecord.input_date_time.toString() === originalKeyList[startIndex]) {
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
                            if(matchingDateFound)
                            {
                                break;
                            }
                            startIndex--;
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
                $scope.series = seriesDates;
                $scope.values = chartDataSets;
            });
            }
            else{
                $scope.status = "Fetch data";
                console.log("Fetch Scores");
                return commonService.apiPost('/metrics/scores', payload).then((data) => {
                    $scope.status = "idle";
                    if(data.length === 0) {
                        $scope.values = null;
                        return;
                    }

                    let values = [];
                    let series = [];
                    let keyList = Object.keys(data.scores);
                    keyList.sort();
                    keyList.forEach((dateTime) => {
                        values.push(data.scores[dateTime].score);
                        let d = new Date(dateTime * 1000).toISOString();
                        //let dateSeries = d.setUTCSeconds(dateTime);
                        series.push(d);
                    });

                    $scope.shortenKeyList(series);
                    if(series.length === 0)
                    {
                        $scope.series = null;
                        $scope.value = null;
                    }
                    else {
                        series = $scope.fixMissingDates(series);
                        series = $scope.getDatesByTimeModeForContainers(series);
                        let valuesByTime = [];
                        keyList.forEach((dateTime) => {
                            //values.push(data.scores[dateTime].score);
                            let d = new Date(dateTime * 1000).toISOString();
                            for(let i = 0; i < series.length; i++)
                            {
                                if(d === series[i])
                                {
                                    valuesByTime.push(data.scores[dateTime].score);
                                }
                            }
                            //let dateSeries = d.setUTCSeconds(dateTime);
                            //series.push(d);
                        });
                        $scope.values = [{data: valuesByTime}];
                        let seriesDates = [];
                        const monthNames = ["null", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

                        series.forEach(function(seriesValues){
                            let s = "Error";
                            let r = /(\d{4})-(\d{2})-(\d{2})/g;
                            let match = r.exec(seriesValues);

                            if ($scope.timeMode === "month") {
                                if (match) {
                                    let month = parseInt(match[2]);
                                    s = monthNames[month];
                                }
                            }
                            else {
                                if (match) {
                                    s = match[2] + "/" + match[3];
                                }
                            }
                            seriesDates.push(s);
                        });
                        $scope.series = seriesDates;

                        $scope.status = "idle";
                        //let keyList = Array.from(keySet);
                    }


                });
            }
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
                    showingTable: '<',
                    tableInfo: '<',
                    chartInfo: '<',
                    waitTime: '='
                  },
        controller: FunMetricChartController
 });
