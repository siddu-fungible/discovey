(function (angular) {
    'use strict';

    function CatalogController($scope, $http, $window, commonAlert) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.getCatalog();
            $scope.currentCatalog = null;
        };

        $scope.getCatalog = function () {
            $http.get('/tcm/catalog').then(function (result){
                $scope.currentCatalog = result.data;

                let data = result.data;
                if(!data["status"]) {
                    commonAlert.showError("Catalog " + payload["name"] + " Create failed: " + data["error_message"])
                }

            }).catch(function(result) {
                commonAlert.showError("Unable to fetch catalog." + result.data.toString());
            });
        }
    }

    angular.module('qa-dashboard').controller("catalogController", CatalogController)


})(window.angular);
