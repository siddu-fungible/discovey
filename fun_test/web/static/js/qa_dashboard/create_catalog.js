(function (angular) {
    'use strict';

    function CreateCatalogController($scope, $http, $window, commonAlert) {
        let ctrl = this;

        ctrl.$onInit = function () {
            console.log("CreateCatalogController");
        };


        $scope.changed = function () {
            commonAlert.closeAllAlerts();
        };

        $scope.submitClick = function (formIsValid) {
            commonAlert.closeAllAlerts();
            if(!$scope.selectedCategory) {
                return commonAlert.showError("Please select a category");
            }
            if(!$scope.catalogName) {
                return commonAlert.showError("Please enter a category name");
            }
            if(!$scope.jql) {
                return commonAlert.showError("Please enter a JQL");
            }

            let payload = {};
            payload["category"] = $scope.selectedCategory;
            payload["name"] = $scope.catalogName;
            payload["jql"] = $scope.jql;

            $http.post('/tcm/create_catalog', payload).then(function (result) {
                let data = result.data;
                if(data["status"]) {
                    commonAlert.showSuccess("Catalog " + payload["name"] + " Created");
                } else {
                    commonAlert.showError("Catalog " + payload["name"] + " Create failed: " + data["error_message"])
                }

            }).catch(function(result) {
                commonAlert.showError("Unable to create a catalog." + result.data.toString());
            });
        }

    }

    angular.module('qa-dashboard').controller("createCatalogController", CreateCatalogController)


})(window.angular);
