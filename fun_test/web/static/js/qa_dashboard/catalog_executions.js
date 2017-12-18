(function (angular) {

'use strict';

function CatalogExecutionsController($scope, $http, $window, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.catalogExecutionSummary = null;
        $scope.fetchCatalogExecutionSummary();
    };

    $scope.fetchCatalogExecutionSummary = function () {
        let message = "Fetch Catalog execution summary";
        $http.get("/tcm/catalog_suite_execution_summary/" + ctrl.catalogName).then(function (result) {
            if (!commonService.validateApiResult(result, message)) {
                return;
            }
            let data = result.data.data;
            $scope.catalogExecutionSummary = data;

        }).catch(function (result) {
            return commonService.showHttpError(message, result);
        });
    };
}


angular.module('qa-dashboard').component('catalogExecutions', {
    templateUrl: '/static/qa_dashboard/catalog_executions.html',
    controller: CatalogExecutionsController,
    bindings: {
        catalogName: '@'
    },
});
})(window.angular);
