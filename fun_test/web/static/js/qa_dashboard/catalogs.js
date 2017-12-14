(function (angular) {
    'use strict';

    function CatalogsController($scope, $http, $window, $timeout, commonAlert) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.categories = [];
            $scope.fetchSummaries();
            $scope.summaries = null;
            $scope.selectedCatalog = null;
            $scope.showExecuteOptions = false;
        };
        
        $scope.fetchCategories = function () {
            $http.get("/tcm/catalog_categories").then(function (result) {
                $scope.categories = angular.fromJson(result.data);

            }).catch(function (result) {
                commonAlert.showError("Unable to retrieve catalog categories: " + result.toString());
            })
        };

        $scope.fetchSummaries = function () {
            $http.get("/tcm/catalogs_summary").then(function (result) {
                let data = result["data"];
                if(!data["status"]) {
                    commonAlert.showHttpError("Unable to get catalog summaries", result);
                    return;
                }
                $scope.summaries = data.data;

            }).catch(function (result) {
                commonAlert.showHttpError("Unable to retrieve catalog summaries: ", result);
            })
        };

        $scope.removeClick = function (catalogName) {
            if (confirm("Are you sure you want to remove " + catalogName + " ?")) {
                $http.get("/tcm/remove_catalog/" + catalogName).then(function (result) {
                    let data = result["data"];
                    if(!data["status"]) {
                        commonAlert.showHttpError("Unable to remove", result);
                        return;
                    }
                    commonAlert.showSuccess("Removing catalog... Please wait", -1);
                    $timeout(function () {
                        $window.location.reload();
                    }, 3000);
                }).catch(function (result) {
                    commonAlert.showHttpError("Unable to remove catalog: ", result);
                })
            }
        };

        $scope.executeClick = function () {
            $scope.showExecuteOptions = !$scope.showExecuteOptions;
        };

    }

    angular.module('qa-dashboard').controller("catalogsController", CatalogsController)


})(window.angular);
