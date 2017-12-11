(function (angular) {
    'use strict';

    function CatalogController($scope, $http, commonAlert) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.getCatalog();
            $scope.currentCatalog = null;
            $scope.jqls = [];
            $scope.showPreview = false;
            $scope.operators = ["or", "and"];
            $scope.selectedOperator = $scope.operators[0];
        };

        $scope.getCatalog = function () {
            $http.get('/tcm/catalog').then(function (result){

                let data = result.data;
                if(!data["status"]) {
                    commonAlert.showError("Catalog fetch failed: " + data["error_message"]);
                    return;
                }
                $scope.currentCatalog = result.data.data;
                let jqlList = $scope.toList($scope.currentCatalog["jqls"]);
                jqlList.forEach(function (element) {
                    $scope.jqls.push({"value": element,
                    "status": "Committed"});
                });

            }).catch(function(result) {
                commonAlert.showError("Unable to fetch catalog." + result.data.toString());
            });
        };

        $scope.toList = function (jsonString) {
            return angular.fromJson(jsonString);
        };

        $scope.removeClick = function (jqlIndex) {
            commonAlert.closeAllAlerts();
            console.log(jqlIndex);
            if (jqlIndex === 0) {
                commonAlert.showError("Cannot remove index 0", 5000);
                return;
            }
            let thisJql = $scope.jqls[jqlIndex];
            if (confirm("Are you sure you want to remove " + thisJql.value + " ?")) {
                if ($scope.jqls.length < 2) {
                    commonAlert.showError("At least one JQL is required", 5000);
                    return;
                }

                $scope.jqls.splice(jqlIndex, 1)
            }

        };

        $scope.previewClick = function () {
            let payload = {};
            let jqlsWithOperator = [];
            $scope.jqls.forEach(function(element) {
                if (element.operator) {
                    jqlsWithOperator.push(element.operator + " " + element.value);
                } else {
                    jqlsWithOperator.push(element.value);
                }
            });
            $http.post("/regression/tcm/preview_catalog", payload).then(function (result) {

                payload["jqls"] = $scope.jqls;
            }).catch(function (result) {

            });

        };

        $scope.addJqlClick = function () {
            if (!$scope.addJql) {
                return;
            }
            $scope.jqls.push({"value": $scope.addJql,
            "status": "Uncommitted",
            "operator": $scope.selectedOperator});
            $scope.showPreview = true;
        }
    }

    angular.module('qa-dashboard').controller("catalogController", CatalogController)


})(window.angular);
