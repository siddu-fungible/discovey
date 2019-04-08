(function (angular) {
    'use strict';

    function CreateCatalogController($scope, $http, commonService) {
        let ctrl = this;

        ctrl.$onInit = function () {
            console.log("CreateCatalogController");
        };


        $scope.changed = function () {
            commonService.closeAllAlerts();
        };

        $scope.submitClick = function (formIsValid) {
            commonService.closeAllAlerts();
            if(!$scope.selectedCategory) {
                return commonService.showError("Please select a category");
            }
            if(!$scope.catalogName) {
                return commonService.showError("Please enter a category name");
            }
            if(!$scope.jql) {
                return commonService.showError("Please enter a JQL");
            }

            let payload = {};
            payload["category"] = $scope.selectedCategory;
            payload["name"] = $scope.catalogName;
            payload["jql"] = $scope.jql;

            $http.post('/tcm/create_catalog', payload).then(function (result) {
                let data = result.data;
                if(data["status"]) {
                    commonService.showSuccess("Catalog " + payload["name"] + " Created");
                } else {
                    commonService.showError("Catalog " + payload["name"] + " Create failed: " + data["error_message"])
                }

            }).catch(function(result) {
                commonService.showError("Unable to create a catalog." + result.data.toString());
            });
        }

    }

    angular.module('qa-dashboard').controller("createCatalogController", CreateCatalogController)


})(window.angular);
