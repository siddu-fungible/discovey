'use strict';

function MetricsSummaryController($scope, commonService, $timeout, $window) {
    let ctrl = this;

    this.$onInit = function () {

        $scope.treeModel = [
            {
                info: "",
                showInfo: false,
                label: "Total",
                trend: "up",
                goodness: 5.6,
                "children": [
                    {
                        info: "",
                        showInfo: false,
                        label: "Software",
                        goodness: 7.5,
                        children: [{info: "", label: "Nucleus", trend: "down", goodness: 6.6, children: [{
                            info: "",
                            goodness: 1.0,
                            label: "Best time for 1 malloc/free (WU)",
                            status: false,

                        }, {
                            info: "",
                            goodness: 3.0,
                            label: "Best time for 1 malloc/free (Threaded)",
                            status: true,

                        }]},
                            {info: "", label: "Storage"}]
                    },
                    {
                        info: "",
                        showInfo: false,
                        label: "Hardware",
                        children: [{info: "", label: "leaf3"}]
                    }
                ]
            }

        ];

        $scope.numGridColumns = 5;
        if(angular.element($window).width() <=1441) {
            $scope.numGridColumns = 3;
        }

        $scope.mode = null;
        $scope.fetchJenkinsJobIdMap();

        $scope.flatNodes = [];
        $scope.metricMap = {};
        $scope.fetchRootMetricInfo("Total", "MetricContainer").then((data) => {
            let metricId = data.metric_id;
            let p1 = {metric_id: metricId};
            commonService.apiPost('/metrics/metric_info', p1).then((data) => {
                let newNode = $scope.getNodeFromData(data);
                newNode.guid = $scope.guid();
                newNode.hide = false;
                newNode.indent = 0;
                $scope.flatNodes.push(newNode);
                $scope.expandNode(newNode);
                $scope.collapsedAll = true;
            });
            return data;
        });


        $scope.goodnessTrendValues = null;
        $scope.inner = {};
        $scope.inner.nonAtomicMetricInfo = "";
        $scope.currentNodeChildrenGuids = null;
        //console.log($scope.treeModel[0][0].showInfo);
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
            positive: data.positive,
            numChildrenPassed: data.num_children_passed,
            numChildrenFailed: data.num_children_failed

        };
        $scope.metricMap[newNode.metricId] = {chartName: newNode.chartName};
        if (newNode.info === "") {
            newNode.info = "<p>Please update the description</p>";
        }

        angular.forEach(newNode.childrenWeights, (info, childId) => {
            newNode.children[childId] = {weight: newNode.childrenWeights[childId], editing: false};
        });

        $scope.evaluateGoodness(newNode, data.goodness_values, data.children_goodness_map);
        /*
        newNode.goodness = Number(data.goodness_values[data.goodness_values.length - 1].toFixed(1));
        newNode.goodnessValues = data.goodness_values;
        newNode.trend = "flat";
        let penultimateGoodness = Number(data.goodness_values[data.goodness_values.length - 2].toFixed(1));
        if (penultimateGoodness > newNode.goodness) {
            newNode.trend = "down";
        } else if (penultimateGoodness < newNode.goodness) {
            newNode.trend = "up";
        }*/

        newNode.status = data.status_values[data.status_values.length - 1];

        let newNodeChildrenIds = JSON.parse(data.children);
        if (newNodeChildrenIds.length > 0) {
            newNode.numChildren = newNodeChildrenIds.length;
        }

        return newNode;
    };

    $scope.evaluateGoodness = (node, goodness_values, children_goodness_map) => {
        node.goodness = Number(goodness_values[goodness_values.length - 1].toFixed(1));
        node.goodnessValues = goodness_values;
        node.childrenGoodnessMap = children_goodness_map;
        node.trend = "flat";
        let penultimateGoodness = Number(goodness_values[goodness_values.length - 2].toFixed(1));
        if (penultimateGoodness > node.goodness) {
            node.trend = "down";
        } else if (penultimateGoodness < node.goodness) {
            node.trend = "up";
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
        $scope.showingNodeInfo = !$scope.showingNodeInfo;
        $scope.currentNodeInfo = "S";
        if (node.positive) {
            $scope.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(last actual value/expected value) * 100&nbsp)/n";
        } else {
            $scope.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(expected value/last actual value) * 100&nbsp)/n";
        }
        $scope.currentNodeInfo += "&nbsp, where n is the number of data-sets";
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

    $scope.submitDescription = (node) => {
        let payload = {};
        payload["metric_model_name"] = node.metricModelName;
        payload["chart_name"] = node.chartName;
        payload["description"] = $scope.inner.nonAtomicMetricInfo;
        commonService.apiPost('/metrics/update_chart', payload, "EditDescription: Submit").then((data) => {
            if (data) {
                alert("Submitted");
            } else {
                alert("Submission failed. Please check alerts");
            }
        });
        $scope.editingDescription = false;

    };

    $scope.xAxisFormatter = (value) => {
        let s = "Error";
        /*
        let key = parseInt(value);
        if (key in $scope.buildInfo) {
            s = $scope.buildInfo[key]["software_date"].toString();
            let thisYear = new Date().getFullYear();
            s = s.replace(thisYear, "");
            let r = /(\d\d+)(\d\d)/g;
            let match = r.exec(s);
            s = match[1] + "/" + match[2];
        }*/

        let r = /(\d{4})-(\d{2})-(\d{2})/g;
        let match = r.exec(value);
        if (match) {
            s = match[2] + "/" + match[3];
        } else {
            let i = 0;
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
        let s = "";
        
        if (key in $scope.buildInfo) {
            softwareDate = $scope.buildInfo[key]["software_date"];
            hardwareVersion = $scope.buildInfo[key]["hardware_version"];
            sdkBranch = $scope.buildInfo[key]["fun_sdk_branch"]
            s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
            s += "<b>Software date:</b> " + softwareDate + "<br>";
            s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
            s += "<b>Git commit:</b> " + $scope.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "")  + "<br>";
            s += "<b>Value:</b> " + y + "<br>";
        } else {
            s += "<b>Value:</b> " + y + "<br>";
        }

        return s;
    };

    $scope.fetchMetricInfoById = (node) => {
        let thisNode = node;
        let p1 = {metric_id: node.metricId};
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

    $scope.getStatusHtml = (node) => {
        let s = "";
        if (node.leaf) {
            if (node.hasOwnProperty("status")) {
                if (node.status === true) {
                    s = "<label class=\"label label-success\">PASSED</label>";
                } else {
                    s = "<label class=\"label label-danger\">FAILED</label>";
                }
                if ((!node.hasOwnProperty("numChildren") && (!node.leaf)) || ((node.numChildren === 0) && !node.leaf)) {
                    s = "<p style='background-color: white' class=\"\">No Data</p>";
                }
            }
        } else {
            s = "<p><span style='color: green'>&#10003;:</span><b>" + node.numChildrenPassed + "</b>" + "&nbsp" ;
            s += "<span style='color: red'><i class='fa fa-close'>:</i></span><b>" + node.numChildrenFailed + "</b></p>"
        }
        return s;
    };

    $scope.getTrendHtml = (node) => {
        let s = "";
        if (node.hasOwnProperty("trend")) {
            if (node.trend === "up") {
                s = "<icon class=\"fa fa-arrow-up aspect-trend-icon fa-icon-green\"></icon>";
            } else if (node.trend === "down") {
                s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>";
            }
        }
        return s;
    };

    $scope.showNonAtomicMetric = (node) => {
        $scope.expandNode(node);
        $scope.mode = "showingNonAtomicMetric";
        $scope._setupGoodnessTrend(node);
        $scope.inner.nonAtomicMetricInfo = node.info;
        $scope.currentNode = null;
        $scope.currentNode = node;
        let payload = {
            metric_model_name: "MetricContainer",
            chart_name: node.chartName
        };


        if (node.chartName === "All metrics") {
            return;
        }
        return commonService.apiPost('/metrics/get_leaves', payload, 'test').then((leaves) => {
            let flattenedLeaves = {};
            $scope.flattenLeaves("", flattenedLeaves, leaves);

            $scope.prepareGridNodes(flattenedLeaves);
            console.log(angular.element($window).width());

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

    $scope.prepareGridNodes = (flattenedNodes) => {
        $scope.grid = [];
        let rowIndex = 0;
        Object.keys(flattenedNodes).forEach((key) => {
            if ($scope.grid.length - 1 < rowIndex) {
                $scope.grid.push([]);
            }
            $scope.grid[rowIndex].push(flattenedNodes[key]);
            if ($scope.grid[rowIndex].length === $scope.numGridColumns) {
                rowIndex++;
            }

        });
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

        $scope.goodnessTrendChartTitle = "Score Trend" ;
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

        $scope.fetchMetricInfoById({metricId: childId}).then((data) => {
            if (!alreadyInserted) {
                let newNode = $scope.getNodeFromData(data);
                newNode.guid = $scope.guid();
                thisNode.lineage.forEach((ancestor) => {
                   newNode.lineage.push(ancestor);
                });
                newNode.lineage.push(thisNode.guid);
                node.childrenGuids.push(newNode.guid);

                newNode.indent = thisNode.indent + 1;
                let index = $scope.getIndex(thisNode);
                $scope.flatNodes.splice(index + 1, 0, newNode);
                $scope._insertNewNode(thisNode, thisChildrenIds, thisAll);
                newNode.hide = false;
                if (thisAll) {
                    $scope.expandNode(newNode, thisAll);
                }
            } else {
                node.childrenGuids.forEach((childGuid) => {
                   let childNode = $scope.flatNodes[$scope.getIndex({guid: childGuid})];
                   //let childrenIds = JSON.parse(data.children);
                   childNode.hide = false;

                });

                $scope._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
            }

        });


    };

    $scope.refreshNode = (node) => {
        let payload = {metric_id: node.metricId};
        commonService.apiPost('/metrics/metric_info', payload).then((data) => {
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

            $scope.fetchMetricInfoById(node).then((data) => {
                let childrenIds = JSON.parse(data.children);
                $scope._insertNewNode(node, childrenIds, all, node.childrenFetched);
                node.childrenFetched = true;
            });

        }
        node.hide = false;
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





