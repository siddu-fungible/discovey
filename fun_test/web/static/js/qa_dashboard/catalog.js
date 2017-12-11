(function (angular) {
    'use strict';

    function CatalogController($scope, $http, $window, commonAlert) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.getCatalog();
            $scope.currentCatalog = null;
            $scope.jqls = [];
        };

        $scope.getCatalog = function () {
            $http.get('/tcm/catalog').then(function (result){

                let data = result.data;
                if(!data["status"]) {
                    commonAlert.showError("Catalog fetch failed: " + data["error_message"]);
                    return;
                }
                $scope.currentCatalog = result.data.data;
                $scope.jqls = angular.fromJson($scope.currentCatalog["jqls"]);

            }).catch(function(result) {
                commonAlert.showError("Unable to fetch catalog." + result.data.toString());
            });
        };

        $scope.toList = function (jsonString) {
            return angular.fromJson(jsonString);
        };

        $scope.removeClick = function (jqlIndex) {
            console.log(jqlIndex);
            let thisJql = $scope.jqls[jqlIndex];
            if (confirm("Are you sure you want to remove " + thisJql + " ?")) {
                alert("deleted"+ s);
            }
        };
    }

    angular.module('qa-dashboard').controller("catalogController", CatalogController)


})(window.angular);
