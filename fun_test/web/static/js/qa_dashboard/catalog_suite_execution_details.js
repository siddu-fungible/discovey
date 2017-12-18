(function (angular) {

'use strict';

function CatalogSuiteExecutionDetailsController($scope, $http, $window, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.fetchCatalogSuiteExecutionDetails();
    };

    $scope.fetchBasicIssueAttributes = function () {
        let message = "fetchBasicIssueAttributes";
        let jira_ids = [];
        angular.forEach($scope.executionDetails, function (value, key) {
            jira_ids.push(key);
        });
        commonService.apiPost("/tcm/basic_issue_attributes", jira_ids, message).then(function (issuesAttributes) {
            if(issuesAttributes) {
                angular.forEach($scope.executionDetails, function (value, key) {
                    value.summary = issuesAttributes[parseInt(key)].summary;
                });
            }
        });
    };

    $scope.fetchCatalogSuiteExecutionDetails = function () {
        let message = "fetchCatalogSuiteExecutionDetails";
        $http.get('/tcm/catalog_suite_execution_details/' + ctrl.instanceName).then(function (result) {
            if (!commonService.validateApiResult(result, message)) {
                return;
            }
            $scope.executionDetails = result["data"]["data"];

            // Fetch basic issue attributes
            return $scope.fetchBasicIssueAttributes();
        }).catch(function (result) {
            return commonService.showHttpError(message, result);
        });
    };



}

angular.module('qa-dashboard').component('catalogSuiteExecutionDetails', {
    templateUrl: '/static/qa_dashboard/catalog_suite_execution_details.html',
    controller: CatalogSuiteExecutionDetailsController,
    bindings: {
        instanceName: '@'
    },
});
})(window.angular);
