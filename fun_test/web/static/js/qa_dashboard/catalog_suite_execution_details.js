(function (angular) {

'use strict';

function CatalogSuiteExecutionDetailsController($scope, $http, $window, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.fetchCatalogSuiteExecutionDetails();
    };

    $scope.fetchCatalogSuiteExecutionDetails = function () {
        let message = "fetchCatalogSuiteExecutionDetails";
        $http.get('/tcm/catalog_suite_execution_details/' + ctrl.instanceName).then(function (result) {
            if (!commonService.validateApiResult(result, message)) {
                return;
            }
            $scope.executionDetails = result["data"]["data"];
            let i = 0;
        }).catch(function (result) {
            return commonService.showHttpError(message, result);
        });
    }

}

angular.module('qa-dashboard').component('catalogSuiteExecutionDetails', {
    templateUrl: '/static/qa_dashboard/catalog_suite_execution_details.html',
    controller: CatalogSuiteExecutionDetailsController,
    bindings: {
        instanceName: '@'
    },
});
})(window.angular);
