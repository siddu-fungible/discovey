'use strict';

function TestController($scope, $http, commonService, $timeout, $modal) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.onSubmit().then((leaves) => {
            console.log("Here");
            let flattenedLeaves = {};
            let root = {name: "FunOS", children: [leaves], leaf: false};
            $scope.flattenLeaves("", flattenedLeaves, leaves);
            console.log(flattenedLeaves);
            $scope.numGridColumns = 2;
            $scope.prepareGridNodes(flattenedLeaves);
            $scope.chartName = "Best time for 1 malloc/free (Threaded)";
            $scope.modelName = "AllocSpeedPerformance";


        });

    };

    $scope.prepareGridNodes = (flattenedNodes) => {
        $scope.grid = [];
        let rowIndex = 0;
        Object.keys(flattenedNodes).forEach((key) => {
            if ($scope.grid.length - 1 < rowIndex) {
                $scope.grid.push([]);
            }
            $scope.grid[rowIndex].push(flattenedNodes[key]);
            if ($scope.grid[rowIndex].length === 2) {
                rowIndex++;
            }

        });
        console.log($scope.grid);
    };

    $scope.onSubmit = function () {
        let payload = {
            metric_model_name: "MetricContainer",
            chart_name: "FunOS"
        };

        return commonService.apiPost('/metrics/get_leaves', payload, 'test').then((leaves) => {
            return leaves;
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
    }
}


angular.module('qa-dashboard').controller("testController", TestController);


