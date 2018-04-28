'use strict';

function MetricsSummaryController($scope, commonService) {
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

        $scope.fetchJenkinsJobIdMap();

        $scope.flatNodes = [];
        $scope.fetchRootMetricInfo("Total", "MetricContainer").then((data) => {
            let metricId = data.metric_id;
            let p1 = {metric_id: metricId};
            commonService.apiPost('/metrics/metric_info', p1).then((data) => {
                let newNode = $scope.getNodeFromData(data);
                newNode.indent = 0;
                $scope.flatNodes.push(newNode);
                $scope.expandNode(newNode);
            });
            return data;
        });



        //console.log($scope.treeModel[0][0].showInfo);
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
        let index = $scope.flatNodes.map(function(x) {return x.metricId;}).indexOf(node.metricId);
        return index;
    };

    $scope.expandAllNodes = () => {
        $scope.flatNodes.forEach((node) => {
            $scope.expandNode(node, true);
        })
    };

    $scope.getNodeFromData = (data) => {
        let newNode = {
            info: "",
            label: data.chart_name,
            collapsed: true,
            metricId: data.metric_id,
            hide: false,
            leaf: data.leaf,
            chartName: data.chart_name,
            metricModelName: data.metric_model_name
        };
        newNode.goodness = data.goodness_values[data.goodness_values.length - 1].toFixed(1);
        newNode.status = data.status_values[data.status_values.length - 1];
        newNode.trend = "flat";
        let penultimateGoodness = data.goodness_values[data.goodness_values.length - 2].toFixed(1);
        if (penultimateGoodness > newNode.goodness) {
            newNode.trend = "down";
        } else if (penultimateGoodness < newNode.goodness) {
            newNode.trend = "up";
        }

        let newNodeChildrenIds = JSON.parse(data.children);
        if (newNodeChildrenIds.length > 0) {
            newNode.numChildren = newNodeChildrenIds.length;
        }

        return newNode;
    };

    $scope.setCurrentChart = (chartName, metricModelName) => {
        $scope.currentChartName = chartName;
        $scope.currentMetricModelName = metricModelName;
    };

    $scope.fetchRootMetricInfo = (chartName, metricModelName) => {
        let payload = {"metric_model_name": metricModelName, chart_name: chartName};
        return commonService.apiPost('/metrics/chart_info', payload).then((data) => {
            return data;
        });
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

    $scope.getTreeHtml = () => {
        let s = "";

        let node = $scope.treeModel.forEach((node, index) => {
            let indexString = "[" + index + "]";
            s += $scope._getNodeHtml(node, indexString);
        });
        //console.logn(s);
        return s;
    };

    $scope.getStatusHtml = (node) => {
        let s = "";
        if (node.hasOwnProperty("status")) {
            if (node.status === true) {
                s = "<label class=\"label label-success\">PASSED</label>";
            } else {
                s = "<label class=\"label label-danger\">FAILED</label>";
            }
        }
        return s;
    };

    $scope.getTrendHtml = (node) => {
        let s = "<icon class=\"fa fa-arrows-h aspect-trend-icon\"></icon>";
        if (node.hasOwnProperty("trend")) {
            if (node.trend === "up") {
                s = "<icon class=\"fa fa-arrow-up aspect-trend-icon fa-icon-green\"></icon>";
            } else if (node.trend === "down") {
                s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>";
            }
        }
        return s;
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


    $scope.expandNode = (node, all) => {
        node.collapsed = false;
        if (node.hasOwnProperty("numChildren") && (node.numChildren > 0)) {
            let thisNode = node;
            // Fetch children ids

            $scope.fetchMetricInfoById(node).then((data) => {
                let childrenIds = JSON.parse(data.children);
                childrenIds.forEach((childId) => {
                    let p1 = {metric_id: childId};
                    let thisNode = node;
                    commonService.apiPost('/metrics/metric_info', p1).then((data) => {
                        let newNode = $scope.getNodeFromData(data);
                        newNode.indent = thisNode.indent + 1;
                        let index = $scope.getIndex(thisNode);
                        let childIndex = $scope.getIndex(newNode);
                        if (childIndex === -1) {
                            $scope.flatNodes.splice(index + 1, 0, newNode);
                        } else {
                            newNode = $scope.flatNodes[childIndex];
                        }
                        newNode.hide = false;
                        if (all) {
                            $scope.expandNode(newNode, all);
                        }
                    });
                });
            });
        }
    };

    $scope.collapseBranch = (node) => {
        let thisIndex = $scope.getIndex(node);
        if (node.hasOwnProperty("numChildren")) {
            for(let i = 1; i <= node.numChildren; i++) {
                if (!node.collapsed) {
                    $scope.collapseBranch($scope.flatNodes[thisIndex + i]);
                    $scope.flatNodes[thisIndex + i].hide = true;
                    $scope.flatNodes[thisIndex + i].collapsed = true;
                }
            }
        }
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





