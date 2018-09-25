'use strict';


function FunMetricChartController($scope, commonService, $attrs, $q, $timeout) {

    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.showingTable = false;
        $scope.setDefault();
        $scope.chartInfo = ctrl.chartInfo;
        $scope.chartName = ctrl.chartName;
        $scope.modelName = ctrl.modelName;
        $scope.headers = null;
        $scope.metricId = -1;
        $scope.editingDescription = false;
        $scope.inner = {};
        if (ctrl.atomic) {
            $scope.atomic = ctrl.atomic;
        }
        else {
            $scope.atomic = false;
        }
        $scope.previewDataSets = ctrl.previewDataSets;
        $scope.currentDescription = "---";
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
        $scope.buildInfo = null;
        $scope.fetchBuildInfo();
        if (ctrl.pointClickCallback) {
            $scope.pointClickCallback = (point) => {
                if (!$attrs.pointClickCallback) return null;
                ctrl.pointClickCallback()(point);
            };
        }
            $scope.xAxisFormatter = (value) => {
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

    };

    $scope.tooltipFormatter = (x, y) => {
        let softwareDate = "Unknown";
        let hardwareVersion = "Unknown";
        let sdkBranch = "Unknown";
        let gitCommit = "Unknown";
        let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
        let match = r.exec(x);
        let key = "";
        if (match) {
            key = match[1];
        }
        else {
            let reg = /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})/g;
            match = reg.exec(x);
            if(match) {
                key = match[1].replace('T', ' ');
            }
        }
        let s = "Error";

        if ($scope.buildInfo && key in $scope.buildInfo) {
            softwareDate = $scope.buildInfo[key]["software_date"];
            hardwareVersion = $scope.buildInfo[key]["hardware_version"];
            sdkBranch = $scope.buildInfo[key]["fun_sdk_branch"]
            s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
            s += "<b>Software date:</b> " + softwareDate + "<br>";
            s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
            s += "<b>Git commit:</b> " + $scope.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "") + "<br>";
            s += "<b>Value:</b> " + y + "<br>";
        } else {
            s = "<b>Value:</b> " + y + "<br>";
        }

        return s;
    };


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



    $scope.fetchBuildInfo = () => {
        commonService.apiGet('/regression/jenkins_job_id_maps').then((data) => {
            commonService.apiGet('/regression/build_to_date_map').then((data) => {
                $scope.buildInfo = data;
            })
        })
    };

    $scope.showTables = () => {
        if ($scope.showingTable === false)
            $scope.showingTable = true;
        else
            $scope.showingTable = false;
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
            $scope.chartName = ctrl.chartName;
            $scope.modelName = ctrl.modelName;
            $scope.previewDataSets = ctrl.previewDataSets;
            $scope.fetchChartInfo().then(() => {
                $scope.tableInfo = ctrl.tableInfo;
                //$scope.timeMode = ctrl.timeMode;
                //console.log("C I:" + ctrl.chartInfo);
                if ($scope.chartInfo) {
                    $scope.fetchMetricsData($scope.modelName, $scope.chartName, $scope.chartInfo, $scope.previewDataSets); // TODO: Race condition on chartInfo
                } else {
                    $scope.fetchMetricsData($scope.modelName, $scope.chartName, null, $scope.previewDataSets); // TODO: Race condition on chartInfo
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
                if ($scope.chartInfo !== null) {
                    $scope.previewDataSets = $scope.chartInfo.data_sets;
                    $scope.currentDescription = $scope.chartInfo.description;
                    $scope.inner.currentDescription = $scope.currentDescription;
                    $scope.negativeGradient = !$scope.chartInfo.positive;
                    $scope.inner.negativeGradient = $scope.negativeGradient;
                    $scope.leaf = $scope.chartInfo.leaf;
                    $scope.inner.leaf = $scope.leaf;
                    $scope.status = "idle";
                }
                return $scope.chartInfo;
            })
        } else {
            return $q.resolve($scope.chartInfo);
        }

    };

    $scope.getValidatedData = (data, minimum, maximum) => {
        let result = data;
        if(data < 0) {
            data = null;
        }
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
        if ($scope.timeMode === "week") {
            for (let i = len - 1; i >= 0; i = i - 7) {
                if (i >= 7) {
                    filteredDate.push([i, i - 7 + 1]);
                }
                else {
                    filteredDate.push([i, 0]);
                }
            }
            result = filteredDate.reverse();
        }
        else if ($scope.timeMode === "month") {
            let i = len - 1;
            let startIndex = len - 1;
            let latestDate = new Date(dateList[i].replace(/\s+/g, 'T'));
            let latestMonth = latestDate.getUTCMonth();
            while (i >= 0) {
                let currentDate = new Date(dateList[i].replace(/\s+/g, 'T'));
                let currentMonth = currentDate.getUTCMonth();
                if (currentMonth !== latestMonth) {
                    filteredDate.push([startIndex, i + 1]);
                    latestMonth = currentMonth;
                    startIndex = i;
                }
                if (i === 0) {
                    filteredDate.push([startIndex, i]);
                }
                i--;
            }
            result = filteredDate.reverse();
        }
        else {
            for (let i = len - 1; i >= 0; i--) {
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
        if ($scope.timeMode === "week") {
            for (let i = len - 1; i >= 0; i = i - 7) {
                filteredDate.push(dateList[i]);
            }
            result = filteredDate.reverse();
        }
        else if ($scope.timeMode === "month") {
            let i = len - 1;
            let startIndex = len - 1;
            let latestDate = new Date(dateList[i].replace(/\s+/g, 'T'));
            let latestMonth = latestDate.getUTCMonth();
            filteredDate.push(dateList[i]);
            while (i >= 0) {
                let currentDate = new Date(dateList[i].replace(/\s+/g, 'T'));
                let currentMonth = currentDate.getUTCMonth();
                if (currentMonth !== latestMonth) {
                    filteredDate.push(dateList[i]);
                    latestMonth = currentMonth;
                }
                i--;
            }
            result = filteredDate.reverse();
        }
        return result;
    };

    $scope.setTimeMode = (mode) => {
        $scope.timeMode = mode;
        if ($scope.chartInfo) {
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, $scope.chartInfo, $scope.previewDataSets); // TODO: Race condition on chartInfo
        } else {
            $scope.fetchMetricsData(ctrl.modelName, ctrl.chartName, null, $scope.previewDataSets); // TODO: Race condition on chartInfo
        }
    };

    $scope.fetchMetricsData = (metricModelName, chartName, chartInfo, previewDataSets) => {
        $scope.title = chartName;
        if (!chartName) {
            return;
        }
        //$scope.status = "Fetch table meta-data";
        $scope.describeTable(metricModelName).then(function (tableInfo) {
            let payload = {};
            payload["metric_model_name"] = metricModelName;
            payload["chart_name"] = chartName;
            payload["preview_data_sets"] = previewDataSets;
            payload["metric_id"] = -1;
            if (chartInfo) {
                payload["metric_id"] = chartInfo["metric_id"];
                $scope.metricId = chartInfo["metric_id"];
            }
            if (metricModelName !== 'MetricContainer') {
                $scope.status = "idle";
                $scope.tableInfo = tableInfo;

                let filterDataSets = [];
                if (previewDataSets) {
                    filterDataSets = previewDataSets;
                } else {
                    //console.log("Chart Info:" + chartInfo);
                    if (chartInfo) {
                        filterDataSets = chartInfo.data_sets;
                        //console.log("C DS:" + chartInfo.data_sets);
                    }
                }
                $scope.filterDataSets = filterDataSets;

                $scope.status = "Fetch data";

                commonService.apiPost("/metrics/data", payload, "fetchMetricsData").then((allDataSets) => {
                    $scope.status = "idle";
                    if (allDataSets.length === 0) {
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
                        for (let i = 0; i < keyList.length; i++) {
                            let output = null;
                            let total = 0;
                            let count = 0;
                            let matchingDateFound = false;
                            seriesDates.push(originalKeyList[keyList[i][0]]);
                            let startIndex = keyList[i][0];
                            let endIndex = keyList[i][1];
                            while (startIndex >= endIndex) {
                                for (let j = 0; j < oneDataSet.length; j++) {
                                    let oneRecord = oneDataSet[j];
                                    if (oneRecord.input_date_time.toString() === originalKeyList[startIndex]) {
                                        matchingDateFound = true;
                                        let outputName = filterDataSets[dataSetIndex].output.name;
                                        output = oneRecord[outputName];
                                        total += output;
                                        count++;
                                        if (chartInfo && chartInfo.y1_axis_title) {
                                            $scope.chart1YaxisTitle = chartInfo.y1_axis_title;
                                        } else {
                                            $scope.chart1YaxisTitle = tableInfo[outputName].verbose_name;
                                        }
                                        if (ctrl.y1AxisTitle) {
                                            $scope.chart1YaxisTitle = ctrl.y1AxisTitle;
                                        }
                                        $scope.chart1XaxisTitle = tableInfo["input_date_time"].verbose_name;

                                    }
                                }
                                startIndex--;
                            }
                            if(count !== 0) {
                                output = total/count;
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
                    $scope.headers = $scope.tableInfo;
                });
            }
            else {
                $scope.status = "Fetch data";
                console.log("Fetch Scores");
                return commonService.apiPost('/metrics/scores', payload).then((data) => {
                    $scope.status = "idle";
                    if (data.length === 0) {
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
                    if (series.length === 0) {
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
                            for (let i = 0; i < series.length; i++) {
                                if (d === series[i]) {
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

                        // series.forEach(function(seriesValues){
                        //     let s = "Error";
                        //     let r = /(\d{4})-(\d{2})-(\d{2})/g;
                        //     let match = r.exec(seriesValues);
                        //
                        //     if ($scope.timeMode === "month") {
                        //         if (match) {
                        //             let month = parseInt(match[2]);
                        //             s = monthNames[month];
                        //         }
                        //     }
                        //     else {
                        //         if (match) {
                        //             s = match[2] + "/" + match[3];
                        //         }
                        //     }
                        //     seriesDates.push(s);
                        // });
                        $scope.series = series;

                        $scope.status = "idle";
                        //let keyList = Array.from(keySet);
                    }


                });
            }
        });
    };

    $scope.submit = () => {
        //$scope.previewDataSets = $scope.copyChartInfo.data_sets;
        let payload = {};
        payload["metric_model_name"] = $scope.modelName;
        payload["chart_name"] = $scope.chartName;
        payload["data_sets"] = $scope.previewDataSets;
        payload["description"] = $scope.inner.currentDescription;
        payload["negative_gradient"] = $scope.inner.negativeGradient;
        payload["leaf"] = $scope.inner.leaf;
        commonService.apiPost('/metrics/update_chart', payload, "EditChart: Submit").then((data) => {
            if (data) {
                alert("Submitted");
            } else {
                alert("Submission failed. Please check alerts");
            }

        });
        $scope.editingDescription = false;
    };

    $scope.dismiss = () => {
        $scope.editingDescription = false;
    };

    $scope.editDescription = () => {
        $scope.editingDescription = true;
    };

    $scope.changeClass = (divId, buttonId) => {
        let divIdClass = angular.element(document.querySelector(divId));
        divIdClass.removeClass('in');
        let collapseArrow = angular.element(document.querySelector(buttonId));
        collapseArrow.addClass('collapsed');
    };

    // $(window).scroll(function() {
    // if ($(this).scrollTop() > 50 ) {
    //     $('.scrolltop:hidden').stop(true, true).fadeIn();
    // } else {
    //     $('.scrolltop').stop(true, true).fadeOut();
    // }
    // });
    // $(function(){$(".scroll").click(function(){$("html, body").animate({ scrollTop: 0 }, 1000);return false})})
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
        showingTable: '<',
        tableInfo: '<',
        chartInfo: '<',
        waitTime: '=',
        atomic: '<'
    },
    controller: FunMetricChartController
});
