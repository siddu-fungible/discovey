'use strict';

function MetricsSummaryController($scope, commonService, $timeout, $window, $q) {
    let ctrl = this;

    this.$onInit = function () {
        $scope.getLastStatusUpdateTime();
        $scope.numGridColumns = 2;
        if(angular.element($window).width() <=1441) {
            $scope.numGridColumns = 2;
        }

        $scope.mode = null;
        $scope.fetchJenkinsJobIdMap();

        $scope.flatNodes = [];
        $scope.metricMap = {};
        $scope.cachedNodeInfo = {};
        $scope.fetchRootMetricInfo("Total", "MetricContainer").then((data) => {
            let metricId = data.metric_id;
            let p1 = {metric_id: metricId};
            commonService.apiPost('/metrics/metric_info', p1).then((data) => {
                $scope.populateNodeInfoCache(data);
                let newNode = $scope.getNodeFromData(data).then((newNode) => {
                    newNode.guid = $scope.guid();
                    newNode.hide = false;
                    newNode.indent = 0;
                    $scope.flatNodes.push(newNode);
                    $scope.expandNode(newNode);
                    $scope.collapsedAll = true;
                });

            });
            return data;
        });


        $scope.goodnessTrendValues = null;
        $scope.inner = {};
        $scope.inner.nonAtomicMetricInfo = "";
        $scope.currentNodeChildrenGuids = null;

        $scope.validDates = null;
        //console.log($scope.treeModel[0][0].showInfo);
    };


    $scope.clearNodeInfoCache = () => {
        $scope.cachedNodeInfo = {};
    };

    $scope.populateNodeInfoCache = (data) => {
        if (!(data.metric_id in $scope.cachedNodeInfo)) {
            $scope.cachedNodeInfo[data.metric_id] = data;
        }
        angular.forEach(data.children_info, (value, key) => {
           $scope.cachedNodeInfo[key] = value;
           angular.forEach(value.children_info, (v2, key2) => {
               $scope.populateNodeInfoCache(v2);
           });
        });
    };

    $scope.getLastStatusUpdateTime = () => {
        commonService.apiGet('/common/time_keeper/' + "last_status_update").then((data) => {
            $scope.lastStatusUpdateTime = data;
        })
    };

    $scope.guid = () => {
      function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
          .toString(16)
          .substring(1);
      }
      return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
    };

    $scope.fetchJenkinsJobIdMap = () => {
        commonService.apiGet('/regression/jenkins_job_id_maps').then((data) => {
            $scope.jenkinsJobIdMap = data;
            //console.log($scope.jenkinsJobIdMap);
            commonService.apiGet('/regression/build_to_date_map').then((data) => {
                $scope.buildInfo = data;
            })
        })
    };

    $scope.getIndex = (node) => {
        let index = $scope.flatNodes.map(function(x) {return x.guid;}).indexOf(node.guid);
        return index;
    };

    $scope.getNode = (guid) => {
        return $scope.flatNodes[$scope.getIndex({guid: guid})];
    };

    $scope.expandAllNodes = () => {
        $scope.flatNodes.forEach((node) => {
            $scope.expandNode(node, true);
        });
        $scope.collapsedAll = false;
        $scope.expandedAll = true;
    };

    $scope.collapseAllNodes = () => {
        $scope.collapseNode($scope.flatNodes[0]);
        $scope.expandedAll = false;
        $scope.collapsedAll = true;
    };

    $scope.getDateBound = (dt, lower) => {
        let newDay = new Date(dt);
        if (lower) {
            newDay.setHours(0, 0, 1);
        } else {
            newDay.setHours(23, 59, 59);
        }

        return newDay;
    };

    function isSameDay(d1, d2) {
          return d1.getFullYear() === d2.getUTCFullYear() &&
            d1.getUTCMonth() === d2.getUTCMonth() &&
            d1.getUTCDate() === d2.getUTCDate();
    }

    $scope.getYesterday = (today) => {
        let yesterday = new Date(today);
        yesterday = yesterday.setDate(yesterday.getDate() - 1);
        return yesterday;
    };


    $scope.getDateRange = () => {
        let today = new Date();
        console.log(today);
        let startMonth = 4 - 1;
        let startDay = 1;
        let startMinute = 59;
        let startHour = 23;
        let startSecond = 1;
        let fromDate = new Date(today.getFullYear(), startMonth, startDay, startHour, startMinute, startSecond);
        fromDate = $scope.getDateBound(fromDate, true);
        // console.log(fromDate);
        // console.log($scope.getDateBound(fromDate, true));
        // console.log($scope.getDateBound(fromDate, false));

        let yesterday = $scope.getYesterday(today);
        let toDate = new Date(yesterday);
        toDate = $scope.getDateBound(toDate, false);
        //let fromDate = new Date();
        // fromDate.setDate(toDate.getDate() - 7);
        // fromDate = $scope.getDateBound(fromDate, true);
        return [fromDate, toDate];

    };

    $scope.getNodeFromData = (data) => {
        let newNode = {
            info: data.description,
            label: data.chart_name,
            collapsed: true,
            metricId: data.metric_id,
            hide: true,
            leaf: data.leaf,
            chartName: data.chart_name,
            metricModelName: data.metric_model_name,
            childrenWeights: JSON.parse(data.children_weights),
            children: {},
            lineage: [],
            numChildDegrades: data.last_num_degrades,
            positive: data.positive,
            numChildrenPassed: data.num_children_passed,
            numChildrenFailed: data.last_num_build_failed,
            lastBuildStatus: data.last_build_status

        };
        /*if (data.chart_name === "BLK_LSV: Latency") {
            let j = 0;
        }*/
        $scope.metricMap[newNode.metricId] = {chartName: newNode.chartName};
        if (newNode.info === "") {
            newNode.info = "<p>Please update the description</p>";
        }

        let dateRange = $scope.getDateRange();
        let fromDate = dateRange[0];
        let toDate = dateRange[1];
        return $scope.fetchScores(data.metric_id, fromDate.toISOString(), toDate.toISOString()).then((scoreData) => {
            newNode.childrenScoreMap = scoreData["children_score_map"];
            $scope.evaluateScores(newNode, scoreData["scores"]);
            angular.forEach(newNode.childrenWeights, (info, childId) => {
                newNode.children[childId] = {weight: newNode.childrenWeights[childId], editing: false};
            });

            // $scope.evaluateGoodness(newNode, data.goodness_values, data.children_goodness_map);

            if (newNode.lastBuildStatus === "PASSED") {
                newNode.status = true;
            } else {
                newNode.status = false;
            }

            let newNodeChildrenIds = JSON.parse(data.children);
            if (newNodeChildrenIds.length > 0) {
                newNode.numChildren = newNodeChildrenIds.length;
            }
            return $q.resolve(newNode);
        });


    };

    $scope.fetchScores = (metricId, fromDate, toDate) => {
        let payload = {};
        payload.metric_id = metricId;
        payload.date_range = [fromDate, toDate];
        return commonService.apiPost('/metrics/scores', payload).then((data) => {
            return data;
        });
    };


    $scope.getSumChildWeights = (children) => {
        let sumOfWeights = 0;
        angular.forEach(children, (info, childId) => {
            sumOfWeights += info.weight;
        });
        return sumOfWeights;
    };

    $scope.getScoreTotal = (currentNode) => {
        let children = currentNode.children;
        let scoreTotal = 0;


        angular.forEach(children, (info, childId) => {
            scoreTotal += info.weight * currentNode.childrenScoreMap[childId];
        });

        let lastDate = new Date($scope.validDates.slice(-1)[0] * 1000);
        let lastDateLower = $scope.getDateBound(lastDate, true);
        let lastDateUpper = $scope.getDateBound(lastDate, false);




        return scoreTotal;
    };

    $scope.evaluateScores = (node, scores) => {

        let keys = Object.keys(scores);
        let sortedKeys = keys.sort();
        if (node.chartName === "Total") {
            $scope.validDates = sortedKeys;
        }

        if (Object.keys(scores).length) {

            let mostRecentDateTimestamp = sortedKeys.slice(-1)[0];
            let mostRecentDate = new Date(mostRecentDateTimestamp * 1000);
            console.log(mostRecentDate);
            console.log(scores[mostRecentDateTimestamp].score);
            /*
            let dateRange = $scope.getDateRange();
            let fromDate = dateRange[0].getTime()/1000;
            let toDate = dateRange[1].getTime()/1000;
            let lastEntry = scores[toDate].score;*/
        }
        let goodnessValues = [];
        sortedKeys.forEach((key) => {
            goodnessValues.push(scores[key].score);
        });

        // console.log("Goodness values: " + goodnessValues);

        node.goodnessValues = goodnessValues;
        try {
                node.goodness = Number(goodnessValues[goodnessValues.length - 1].toFixed(1));
        } catch (e) {

        }

        node.childrenGoodnessMap = {};
        node.trend = "flat";
        if (goodnessValues.length > 1) {
            let penultimateGoodness = Number(goodnessValues[goodnessValues.length - 2].toFixed(1));
            if (penultimateGoodness > node.goodness) {
                node.trend = "down";
            } else if (penultimateGoodness < node.goodness) {
                node.trend = "up";
            }
            if (Number(goodnessValues[goodnessValues.length - 1].toFixed(1)) === 0) {
                node.trend = "down";
            }
        }
        console.log("Node: " + node.chartName + " Goodness: " + node.goodness);
    };

    $scope.evaluateGoodness = (node, goodness_values, children_goodness_map) => {
        if (goodness_values.length) {
            try {
                node.goodness = Number(goodness_values[goodness_values.length - 1].toFixed(1));
            } catch (e) {
            }
            node.goodnessValues = goodness_values;
            node.childrenGoodnessMap = children_goodness_map;
            node.trend = "flat";
            let penultimateGoodness = Number(goodness_values[goodness_values.length - 2].toFixed(1));
            if (penultimateGoodness > node.goodness) {
                node.trend = "down";
            } else if (penultimateGoodness < node.goodness) {
                node.trend = "up";
            }
            if (Number(goodness_values[goodness_values.length - 1].toFixed(1)) === 0) {
                node.trend = "down";
            }
        }
    };

    $scope.getLastElement = (array) => {
        let result = null;
        if (array.length) {
            result = array[array.length - 1];
        }
        return result;
    };

    $scope.setCurrentChart = (node) => {
        $scope.mode = "showingAtomicMetric";
        $scope.currentChartName = node.chartName;
        $scope.currentMetricModelName = node.metricModelName;
        $scope.currentNode = node;
    };

    $scope.showNodeInfoClick = (node) => {
        if($scope.currentMetricModelName === 'MetricContainer') {
            $scope.showingContainerNodeInfo = !$scope.showingContainerNodeInfo;
        }
        else {
            $scope.showingNodeInfo = !$scope.showingNodeInfo;
            $scope.currentNodeInfo = null;
            if (node.positive) {
                $scope.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(last actual value/expected value) * 100&nbsp)/n";
            } else {
                $scope.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(expected value/last actual value) * 100&nbsp)/n";
            }
            $scope.currentNodeInfo += "&nbsp, where n is the number of data-sets";
        }
    };


    $scope.fetchRootMetricInfo = (chartName, metricModelName) => {
        let payload = {"metric_model_name": metricModelName, chart_name: chartName};
        return commonService.apiPost('/metrics/chart_info', payload).then((data) => {
            return data;
        });
    };

    $scope.getChildWeight = (node, childMetricId) => {
        if (node.hasOwnProperty("childrenWeights")) {
            return node.childrenWeights[childMetricId];
        } else {
            return 0;
        }
    };

    $scope.editDescriptionClick = () => {
        $scope.editingDescription = true;
    };


    $scope.closeEditingDescriptionClick = () => {
        $scope.editingDescription = false;
    };

    $scope.openAtomicTab = () => {
        let url = "/metrics/atomic/" + $scope.currentChartName + "/" + $scope.currentMetricModelName;
        $window.open(url, '_blank');
    };

    $scope.submitDescription = (node) => {
        let payload = {};
        payload["metric_model_name"] = node.metricModelName;
        payload["chart_name"] = node.chartName;
        payload["description"] = $scope.inner.nonAtomicMetricInfo;

        // TODO: Refresh cache
        commonService.apiPost('/metrics/update_chart', payload, "EditDescription: Submit").then((data) => {
            if (data) {
                alert("Submitted");
            } else {
                alert("Submission failed. Please check alerts");
            }
        });
        $scope.editingDescription = false;

    };

    // $scope.tooltipFormatter = (x, y) => {
    //     let softwareDate = "Unknown";
    //     let hardwareVersion = "Unknown";
    //     let sdkBranch = "Unknown";
    //     let gitCommit = "Unknown";
    //     let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
    //     let match = r.exec(x);
    //     let key = "";
    //     if (match) {
    //         key = match[1];
    //     }
    //     let s = "";
    //
    //     if (key in $scope.buildInfo) {
    //         softwareDate = $scope.buildInfo[key]["software_date"];
    //         hardwareVersion = $scope.buildInfo[key]["hardware_version"];
    //         sdkBranch = $scope.buildInfo[key]["fun_sdk_branch"]
    //         s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
    //         s += "<b>Software date:</b> " + softwareDate + "<br>";
    //         s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
    //         s += "<b>Git commit:</b> " + $scope.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "")  + "<br>";
    //         s += "<b>Value:</b> " + y + "<br>";
    //     } else {
    //         s += "<b>Value:</b> " + y + "<br>";
    //     }
    //
    //     return s;
    // };


    $scope.fetchMetricInfoById = (node) => {
        let thisNode = node;
        let p1 = {metric_id: node.metricId};
        if (node.metricId in $scope.cachedNodeInfo) {
            return $q.resolve($scope.cachedNodeInfo[node.metricId]);
        }
        return commonService.apiPost('/metrics/metric_info', p1).then((data) => {
           return data;
        });
    };


    $scope.testClick = function () {
        console.log("testClick");
        console.log(ctrl.f);
    };

    $scope.showInfoClick = (node) => {
        node.showInfo = !node.showInfo;
    };

    $scope.getConsolidatedTrend = (node) => {
        let numTrendDown = 0;

        if (node.hasOwnProperty("childrenGuids")) {
            node.childrenGuids.forEach((childGuid) => {
                let child = $scope.flatNodes[$scope.getIndex({guid: childGuid})];
                numTrendDown += $scope.getConsolidatedTrend(child);
            });
        } else {
            if (node.trend === "down") {
                numTrendDown += 1;
            }
        }
        return numTrendDown;
    };

    $scope.getStatusHtml = (node) => {
        let s = "";
        if (node.leaf) {
            if (node.hasOwnProperty("status")) {
                if (node.status !== true) {
                    s = "Bld: <label class=\"label label-danger\">FAILED</label>";
                }
                if ((!node.hasOwnProperty("numChildren") && (!node.leaf)) || ((node.numChildren === 0) && !node.leaf)) {
                    s = "<p style='background-color: white' class=\"\">No Data</p>";
                }
            }
        } else {



            //s = "<p><span style='color: green'>&#10003;:</span><b>" + numTrendUp + "</b>" + "&nbsp" ;
            //s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>";
            /*if (node.chartName === "BLK_LSV: Latency") {
                let u = 0;
            }*/
            if(node.chartName !== "All metrics") {
                if (node.numChildDegrades) {
                    s += "<span style='color: red'><i class='fa fa-arrow-down aspect-trend-icon fa-icon-red'>:</i></span>" + node.numChildDegrades + "";
                }
                if (node.numChildrenFailed) {
                    if (node.numChildDegrades) {
                        s += ",&nbsp";
                    }
                    s += "<i class='fa fa-times fa-icon-red'>:</i>" + "<span style='color: black'>" + node.numChildrenFailed + "</span>";
                }
            }
        }
        return s;
    };

    $scope.getTrendHtml = (node) => {
        let s = "";
        if (node.hasOwnProperty("trend")) {
            if (node.chartName === "All metrics")
            {
                node.trend = "flat";
            }
            if (node.trend === "up") {
                s = "<icon class=\"fa fa-arrow-up aspect-trend-icon fa-icon-green\"></icon>&nbsp";
            } else if (node.trend === "down") {
                s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>&nbsp;";
            }
            else if (node.trend === "flat") {
                s = "<icon class=\"fa fa-arrow-down aspect-trend-icon\" style=\"visibility: hidden;\"></icon>&nbsp;";
            }
        }
        return s;
    };

    $scope.isLeafsParent = (node) => {
        let isLeafParent = false; // Parent of a leaf
        if (node.hasOwnProperty("childrenGuids")) {
            node.childrenGuids.forEach((childGuid) => {
                let child = $scope.flatNodes[$scope.getIndex({guid: childGuid})];
                if (child.leaf) {
                    isLeafParent = true;
                }
            });
        }
        return isLeafParent;
    };

    $scope.showNonAtomicMetric = (node) => {
        $scope.resetGrid();
        $scope.mode = "showingNonAtomicMetric";
        $scope.currentNode = node;
        $scope.currentChartName = node.chartName;
        $scope.currentMetricModelName = "MetricContainer";
        $scope.expandNode(node).then(() => {

            //$scope.mode = "showingNonAtomicMetric";
            $scope._setupGoodnessTrend(node);
            $scope.inner.nonAtomicMetricInfo = node.info;
            //$scope.currentNode = null;
           // $scope.currentNode = node;
            // let payload = {
            //     metric_model_name: "MetricContainer",
            //     chart_name: node.chartName
            // };
            //$scope.currentChartName = node.chartName;
            //$scope.currentMetricModelName = "MetricContainer";
            console.log("Before getting leaves");
            if ((node.chartName === "All metrics") || (!$scope.isLeafsParent(node))) {
                return $q.resolve(null);
            } else {
                return $q.resolve(null); // Disable for now
                // commonService.apiPost('/metrics/get_leaves', payload, 'test').then((leaves) => {
                //
                //     let flattenedLeaves = {};
                //     $scope.flattenLeaves("", flattenedLeaves, leaves);
                //     $timeout(()=> {
                //         $scope.prepareGridNodes(flattenedLeaves);
                //     }, 1000);
                //
                //     console.log(angular.element($window).width());
                //
                // });

            }

        });


    };

    $scope.flattenLeaves = function (parentName, flattenedLeaves, node) {
        let myName = node.name;
        if (parentName !== "") {
            myName = parentName + " > " + node.name;
        }
        if (!node.leaf) {
            node.children.forEach((child) => {
                $scope.flattenLeaves(myName, flattenedLeaves, child);
            });
        } else {
            node.lineage = parentName;
            let newNode = {name: node.name, id: node.id, metricModelName: node.metric_model_name};
            flattenedLeaves[newNode.id] = newNode;
        }
    };

    $scope.resetGrid = () => {
        $scope.grid = [];
    };

    $scope.prepareGridNodes = (flattenedNodes) => {
        let maxRowsInMiniChartGrid = 10;
        console.log("Prepare Grid nodes");
        let tempGrid = [];
        let rowIndex = 0;
        Object.keys(flattenedNodes).forEach((key) => {
            if (rowIndex < maxRowsInMiniChartGrid) {
                if (tempGrid.length - 1 < rowIndex) {
                    tempGrid.push([]);
                }
                tempGrid[rowIndex].push(flattenedNodes[key]);
                if (tempGrid[rowIndex].length === $scope.numGridColumns) {
                    rowIndex++;
                }
            }
        });
        $scope.grid = tempGrid;

    };

    $scope._setupGoodnessTrend = (node) => {
        let values = [{
                data: node.goodnessValues
            }];
        $scope.goodnessTrendValues = null;
        $timeout (() => {
            $scope.goodnessTrendValues = values;
        }, 1);

        $scope.charting = true;

        $scope.goodnessTrendChartTitle = node.chartName;
    };

    $scope.getChildrenGuids = (node) => {
        return node.childrenGuids;
    };

    $scope.showGoodnessTrend = (node) => {
        $scope.mode = "showingGoodnessTrend";
        $scope._setupGoodnessTrend(node);
    };

    $scope.getIndentHtml = (node) => {
        let s = "";
        if (node.hasOwnProperty("indent")) {
            for(let i = 0; i < node.indent - 1; i++) {
                s += "<span style=\"color: white\">&rarr;</span>";
            }
            if (node.indent)
                s += "<span>&nbsp;&nbsp;</span>";
        }

        return s;
    };

    $scope.editingWeightClick = (info) => {
        info.editing = true;
        info.editingWeight = info.weight;
    };

    $scope.submitWeightClick = (node, childId, info) => {
        let payload = {};
        payload.metric_id = node.metricId;
        payload.lineage = node.lineage;
        payload.child_id = childId;
        payload.weight = info.editingWeight;
        commonService.apiPost('/metrics/update_child_weight', payload).then((data) => {
            info.weight = info.editingWeight;
            $scope.clearNodeInfoCache();
            if (node.hasOwnProperty("lineage") && node.lineage.length > 0) {
                $scope.refreshNode($scope.getNode(node.lineage[0]));
            } else {
                $scope.refreshNode(node);
            }
        });
        info.editing = false;
    };

    $scope.closeEditingWeightClick = (info) => {
        info.editing = false;
    };


    $scope.collapseNode = (node) => {
        if (node.hasOwnProperty("numChildren")) {
            $scope.collapseBranch(node);
        }
        node.collapsed = true;
    };



    $scope._insertNewNode = (node, childrenIds, all, alreadyInserted) => {
        if (childrenIds.length <= 0) {
            return;
        }
        let thisNode = node;
        let thisAll = all;
        let childId = childrenIds.pop();
        let thisChildrenIds = childrenIds;
        let p1 = {metric_id: childId};
        if (!node.hasOwnProperty("childrenGuids")) {
            node.childrenGuids = [];
        }

        return $scope.fetchMetricInfoById({metricId: childId}).then((data) => {
            if (!alreadyInserted) {
                console.log("!alreadyInserted");
                return $scope.getNodeFromData(data).then((newNode) => {
                    newNode.guid = $scope.guid();
                    thisNode.lineage.forEach((ancestor) => {
                       newNode.lineage.push(ancestor);
                    });
                    newNode.lineage.push(thisNode.guid);
                    console.log("Added childGuid for node:" + node.chartName);
                    node.childrenGuids.push(newNode.guid);

                    newNode.indent = thisNode.indent + 1;
                    let index = $scope.getIndex(thisNode);
                    $scope.flatNodes.splice(index + 1, 0, newNode);
                    $scope._insertNewNode(thisNode, thisChildrenIds, thisAll);
                    newNode.hide = false;
                    if (thisAll) {
                        $scope.expandNode(newNode, thisAll);
                    }
                });

            } else {
                console.log("alreadyInserted");
                node.childrenGuids.forEach((childGuid) => {
                   let childNode = $scope.flatNodes[$scope.getIndex({guid: childGuid})];
                   //let childrenIds = JSON.parse(data.children);
                   childNode.hide = false;

                });

                $scope._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
            }
            return $q.resolve(null);
        });


    };

    $scope.refreshNode = (node) => {
        let payload = {metric_id: node.metricId};
        commonService.apiPost('/metrics/metric_info', payload).then((data) => {
            $scope.populateNodeInfoCache(data);
            $scope.evaluateGoodness(node, data.goodness_values, data.children_goodness_map);
            $scope._setupGoodnessTrend(node);
        });
        if (node.hasOwnProperty("childrenGuids")) {
            node.childrenGuids.forEach((childGuid) => {
                $scope.refreshNode($scope.getNode(childGuid));
            });
        }
    };

    $scope.expandNode = (node, all) => {
        node.collapsed = false;
        if (node.hasOwnProperty("numChildren") && (node.numChildren > 0)) {
            let thisNode = node;
            // Fetch children ids

            return $scope.fetchMetricInfoById(node).then((data) => {
                console.log("Fetching Metrics Info for node:" + node.metricId);
                node.hide = false;
                let childrenIds = JSON.parse(data.children);
                return $scope._insertNewNode(node, childrenIds, all, node.childrenFetched).then(() => {
                    console.log("Inserted: " + node.chartName);
                    node.childrenFetched = true;
                    return $q.resolve(null);
                });

            });

        }
        else {
            return $q.resolve(null);
        }
        //node.hide = false;

    };

    $scope.collapseBranch = (node, traversedNodes) => {
        let thisIndex = $scope.getIndex(node);
        if (node.hasOwnProperty("numChildren")) {
            $scope.hideChildren(node, true);
            /*
            for(let i = 1; i <= node.numChildren; i++) {
                if (!node.collapsed) {
                    traversedNodes += $scope.collapseBranch($scope.flatNodes[thisIndex + traversedNodes + 2]);
                    $scope.flatNodes[thisIndex + traversedNodes + 1].collapsed = true;
                    $scope.flatNodes[thisIndex + traversedNodes + 1].hide = true;
                }
            }*/
        }
        return traversedNodes;
    };

    $scope.hideChildren = (node, root) => {
        let totalHides = 0;
        if (!node) {
            return 0;
        }
        let thisIndex = $scope.getIndex(node);



        if (node.hasOwnProperty("numChildren")) {
            if (!node.childrenFetched) {
                return 0;
            }

            let nextIndex = thisIndex + 1;
            if ((nextIndex >= $scope.flatNodes.length) && (!node.collapsed)) {
                console.log("Huh!");
                return 0;
            }
            for(let i = 1; i <= node.numChildren  && (nextIndex < $scope.flatNodes.length); i++) {
                let hides = 0;
                if (true) {
                    hides += $scope.hideChildren($scope.flatNodes[nextIndex], false);
                }

                $scope.flatNodes[nextIndex].collapsed = true;
                $scope.flatNodes[nextIndex].hide = true;
                totalHides += 1 + hides;
                nextIndex += hides + 1;

            }
        }
        /*
        if (!root) {
            $scope.flatNodes[thisIndex].collapsed = true;
            $scope.flatNodes[thisIndex].hide = true;
            totalHides += 1;
        }*/
        return totalHides;
    };

    $scope.isNodeVisible = (node) => {
        return !node.hide;
    }

}


angular.module('qa-dashboard').directive('dynamic', function ($compile) {
  return {
    restrict: 'A',
    replace: true,
    link: function (scope, ele, attrs) {
      scope.$watch(attrs.dynamic, function(html) {
        ele.html(html);
        $compile(ele.contents())(scope);
      });
    }
  };
});

angular.module('qa-dashboard').controller("metricsSummaryController", MetricsSummaryController);
angular.module('qa-dashboard').filter('unsafe', function($sce) { return $sce.trustAsHtml; });





