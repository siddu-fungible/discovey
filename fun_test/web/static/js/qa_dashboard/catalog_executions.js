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
            $scope.catalogExecutionSummary = result.data.data;
            $scope.catalogExecutionSummary.forEach(function (instance) {
                let instanceName = instance.fields.instance_name;
                let thisInstance = instance;
                thisInstance.fields.numPassed = 0;
                thisInstance.fields.numFailed = 0;
                thisInstance.fields.numTotal = 0;

                commonService.apiGet("/tcm/catalog_suite_execution_details_with_jira/" + instanceName).then(function (data) {

                    angular.forEach(data.jira_ids, function (info, jiraId) {
                        info.instances.forEach(function (instance) {
                           thisInstance.fields.numTotal += 1;
                           if(instance.result === "PASSED") {
                               thisInstance.fields.numPassed += 1;
                           }
                           if(instance.result === "FAILED") {
                               thisInstance.fields.numFailed += 1;
                           }


                        });
                    });
                })
            });

        }).catch(function (result) {
            return commonService.showHttpError(message, result);
        });
    };

    $scope.fetchCatalogSuiteExecutionDetails = function (instanceName) {

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
