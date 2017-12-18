(function (angular) {
    'use strict';

    function CatalogController($scope, $http, commonService) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.currentCatalog = null;
            $scope.jqls = [];
            $scope.showValidate = false;
            $scope.operators = ["or", "and"];
            $scope.selectedOperator = $scope.operators[0];
            $scope.validated = false;
            let catalogElement = angular.element(document.querySelector('#catalog-div'));
            $scope.catalogName = catalogElement.data("catalog-name");
            $scope.getCatalog();

        };

        $scope.setCatalogName = function (name) {
            $scope.catalogName = name;
        };

        $scope.getCatalog = function () {
            $http.get('/tcm/catalog/' + $scope.catalogName).then(function (result){

                let data = result.data;
                if(!data["status"]) {
                    commonService.showError("Catalog fetch failed: " + data["error_message"]);
                    return;
                }
                $scope.currentCatalog = result.data.data;
                let jqlList = $scope.toList($scope.currentCatalog["jqls"]);
                jqlList.forEach(function (element) {
                    $scope.jqls.push({"value": element,
                    "status": "Committed"});
                });

            }).catch(function(result) {
                commonService.showError("Unable to fetch catalog." + result.data.toString());
            });
        };

        $scope.toList = function (jsonString) {
            return angular.fromJson(jsonString);
        };

        $scope.removeClick = function (jqlIndex) {

            commonService.closeAllAlerts();
            console.log(jqlIndex);
            if (jqlIndex === 0) {
                commonService.showError("Cannot remove index 0", 5000);
                return;
            }
            let thisJql = $scope.jqls[jqlIndex];
            if (confirm("Are you sure you want to remove " + thisJql.value + " ?")) {
                if ($scope.jqls.length < 2) {
                    commonService.showError("At least one JQL is required", 5000);
                    return;
                }
                $scope.jqls.splice(jqlIndex, 1)
            }
            $scope.validated = false;
            $scope.showValidate = true;

        };

        $scope.getJqlsWithOperator = function (jqls) {
            let jqlsWithOperator = [];
            jqls.forEach(function (element) {
                if (element.operator) {
                    jqlsWithOperator.push(element.operator + " (" + element.value + ")");
                } else {
                    jqlsWithOperator.push(element.value);
                }
            });

            return jqlsWithOperator;
        };

        $scope.validateClick = function () {
            let payload = {};
            payload["jqls"] = $scope.getJqlsWithOperator($scope.jqls);

            $http.post("/tcm/preview_catalog", payload).then(function (result) {
                let data = result.data;
                if (!data["status"]) {
                    commonService.showError("Catalog preview failed: " + data["error_message"]);
                    return;
                }
                $scope.currentCatalog = result.data.data;
                $scope.validated = true;
            }).catch(function (result) {
                commonService.showError("Unable to preview catalog. " + result.data.toString());

            });

        };

        $scope.addJqlClick = function () {
            if (!$scope.addJql) {
                return;
            }
            $scope.validated = false;
            $scope.jqls.push({"value": $scope.addJql,
            "status": "Uncommitted",
            "operator": $scope.selectedOperator});
            $scope.showValidate = true;
        };

        $scope.commitClick = function () {
            let payload = {};
            payload["name"] = $scope.catalogName;
            payload["jqls"] = $scope.getJqlsWithOperator($scope.jqls);
            $http.post("/tcm/update_catalog", payload).then(function (result) {
                commonService.showSuccess("Committed catalog");
            }).catch(function (result) {
                commonService.showError("Unable to commit catalog. " + result.data.toString());
            });

        }
    }

    angular.module('qa-dashboard').controller("catalogController", CatalogController)


})(window.angular);
