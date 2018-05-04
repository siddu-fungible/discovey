'use strict';

function MetricsSummaryController($scope, commonService, $timeout) {
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
        $scope.mode = null;
        $scope.fetchJenkinsJobIdMap();

        $scope.flatNodes = [];
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
            metricModelName: data.metric_model_name
        };
        if (newNode.info === "") {
            newNode.info = "<p>Please update the description</p>";
        }
        newNode.goodness = Number(data.goodness_values[data.goodness_values.length - 1].toFixed(1));
        newNode.goodnessValues = data.goodness_values;
        newNode.status = data.status_values[data.status_values.length - 1];
        newNode.trend = "flat";
        let penultimateGoodness = Number(data.goodness_values[data.goodness_values.length - 2].toFixed(1));
        if (penultimateGoodness > newNode.goodness) {
            //console.log("Setting down:" + penultimateGoodness + ":" + newNode.goodness);
            newNode.trend = "down";
        } else if (penultimateGoodness < newNode.goodness) {
            newNode.trend = "up";
            //console.log("Setting up:" + penultimateGoodness + ":" + newNode.goodness);
        }
        /*
        console.log(newNode.chartName);
        console.log(newNode.trend);
        console.log(data.goodness_values);
        console.log(newNode.goodness, penultimateGoodness);*/

        let newNodeChildrenIds = JSON.parse(data.children);
        if (newNodeChildrenIds.length > 0) {
            newNode.numChildren = newNodeChildrenIds.length;
        }

        return newNode;
    };

    $scope.setCurrentChart = (chartName, metricModelName) => {
        $scope.mode = "showingAtomicMetric";
        $scope.currentChartName = chartName;
        $scope.currentMetricModelName = metricModelName;
    };

    $scope.fetchRootMetricInfo = (chartName, metricModelName) => {
        let payload = {"metric_model_name": metricModelName, chart_name: chartName};
        return commonService.apiPost('/metrics/chart_info', payload).then((data) => {
            return data;
        });
    };

    $scope.editDescriptionClick = () => {
        $scope.editingDescription = true;
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
        let key = parseInt(value);
        if (key in $scope.buildInfo) {
            s = $scope.buildInfo[key]["software_date"].toString();
            let thisYear = new Date().getFullYear();
            s = s.replace(thisYear, "");
            let r = /(\d\d+)(\d\d)/g;
            let match = r.exec(s);
            s = match[1] + "/" + match[2];
        }
        return s;
    };

    $scope.tooltipFormatter = (x, y) => {
        let softwareDate = "Unknown";
        let hardwareVersion = "Unknown";
        let sdkBranchRef = x;
        let key = parseInt(x);
        if (key in $scope.buildInfo) {
            softwareDate = $scope.buildInfo[key]["software_date"];
            hardwareVersion = $scope.buildInfo[key]["hardware_version"];
        }
        let s = "<b>SDK branch git ref:</b> " + sdkBranchRef + "<br>";
        s += "<b>Software date:</b> " + softwareDate + "<br>";
        s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
        s += "<b>Value:</b> " + y + "<br>";
        return s;
    };

    $scope.fetchMetricInfoById = (node) => {
        let thisNode = node;
        let p1 = {metric_id: node.metricId};
        return commonService.apiPost('/metrics/metric_info', p1).then((data) => {

           return data;
        });
    };

    $scope.flatten = (node, indent) => {
        node.indent = indent;
        node.hide = true;
        node.collapsed = true;
        $scope.flatNodes.push(node);
        if (node.hasOwnProperty("children")) {
            node.children.forEach((node) => {
                $scope.flatten(node, indent + 1);
            });
        }
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
        return s;
    };

    $scope.getTrendHtml = (node) => {
        let s = "";
        if (node.hasOwnProperty("trend")) {
            if (node.trend === "up") {
                s = "<button class='trend-button-green'><icon class=\"fa fa-arrow-up aspect-trend-icon fa-icon-green\"></icon></button>";
            } else if (node.trend === "down") {
                s = "<button class='trend-button-red'><icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon></button>";
            }
        }
        return s;
    };

    $scope.showNonAtomicMetric = (node) => {
        $scope.mode = "showingNonAtomicMetric";
        $scope._setupGoodnessTrend(node);
        $scope.inner.nonAtomicMetricInfo = node.info;
        $scope.currentNode = node;
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

        $scope.goodnessTrendChartTitle = "Goodness Trend";
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
                s += "<span>&#8627;</span>";
        }

        return s;
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
                   let childrenIds = JSON.parse(data.children);
                   childNode.hide = false;

                });

                $scope._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
            }

        });


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





