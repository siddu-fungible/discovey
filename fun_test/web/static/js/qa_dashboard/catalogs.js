(function (angular) {
    'use strict';

    function CatalogsController($scope, $http, $window, $timeout, commonService) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.categories = [];
            $scope.fetchSummaries();
            $scope.summaries = null;
            $scope.selectedCatalog = null;
            $scope.showExecuteOptions = false;
            $scope.owners = [];
            $scope.fetchOwners();
            $scope.instanceName = null;
        };

        $scope.fetchOwners = function () {
            $http.get("/regression/engineers").then(function (result) {
                if(!commonService.validateApiResult(result, "Fetch Engineers")) {
                    return;
                }
                let data = result.data.data;
                data.forEach(function (element) {
                    $scope.owners.push({"name": element.fields.short_name, "email": element.fields.email});
                });

            }).catch(function (result) {
                commonService.showHttpError("Unable to fetch owners", result)
            });
        };

        $scope.fetchCategories = function () {
            $http.get("/tcm/catalog_categories").then(function (result) {
                $scope.categories = angular.fromJson(result.data);

            }).catch(function (result) {
                commonService.showError("Unable to retrieve catalog categories: " + result.toString());
            })
        };

        $scope.fetchSummaries = function () {
            $http.get("/tcm/catalogs_summary").then(function (result) {
                let data = result["data"];
                if(!data["status"]) {
                    commonService.showHttpError("Unable to get catalog summaries", result);
                    return;
                }
                $scope.summaries = data.data;

            }).catch(function (result) {
                commonService.showHttpError("Unable to retrieve catalog summaries: ", result);
            })
        };

        $scope.removeClick = function (catalogName) {
            if (confirm("Are you sure you want to remove " + catalogName + " ?")) {
                $http.get("/tcm/remove_catalog/" + catalogName).then(function (result) {
                    let data = result["data"];
                    if(!data["status"]) {
                        commonService.showHttpError("Unable to remove", result);
                        return;
                    }
                    commonService.showSuccess("Removing catalog... Please wait", -1);
                    $timeout(function () {
                        $window.location.reload();
                    }, 3000);
                }).catch(function (result) {
                    commonService.showHttpError("Unable to remove catalog: ", result);
                })
            }
        };

        $scope.executeClick = function () {
            $scope.showExecuteOptions = !$scope.showExecuteOptions;
        };

        $scope.executeSubmitClick = function () {
            console.log($scope.selectedOwner);
            if (!$scope.selectedOwner) {
                return commonService.showError("Please choose an owner");
            }
            if (!$scope.instanceName) {
                return commonService.showError("Please enter an instance name");
            }
            let payload = {};
            payload["name"] = $scope.selectedCatalog;
            payload["owner_email"] = $scope.selectedOwner.email;
            payload["instance_name"] = $scope.instanceName;
            $http.post("/tcm/execute_catalog", payload).then(function (result) {
                if (!commonService.validateApiResult(result, "Execute catalog")) {
                    return;
                }
                commonService.showSuccess("Catalog execution instance created");

            }).catch(function (result) {
                return commonService.showHttpError("Execute catalog", result);
            });
        };

    }

    angular.module('qa-dashboard').controller("catalogsController", CatalogsController);

})(window.angular);
