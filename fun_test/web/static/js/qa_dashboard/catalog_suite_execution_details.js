(function (angular) {

'use strict';

function CatalogSuiteExecutionDetailsController($scope, $http, $window, resultToClass, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.fetchCatalogSuiteExecutionDetails();
        $scope.overrideOptions = ["PASSED", "FAILED"];  //TODO
    };

    $scope.resultToClass = function (result) {
        return resultToClass(result);
    };

    $scope.fetchBasicIssueAttributes = function () {
        let message = "fetchBasicIssueAttributes";
        let jiraIds = [];
        angular.forEach($scope.executionDetails, function (value, key) {
            jiraIds.push(key);
        });
        commonService.apiPost("/tcm/basic_issue_attributes", jiraIds, message).then(function (issuesAttributes) {
            if(issuesAttributes) {
                angular.forEach($scope.executionDetails, function (value, key) {
                    value.summary = issuesAttributes[parseInt(key)].summary;
                    value.components = issuesAttributes[parseInt(key)].components;
                    let jiraId = null;
                    if(Object.keys($scope.executionDetails)) {

                    }
                    jiraIds.forEach(function (jiraId) {
                        let suiteExecutionId = $scope.executionDetails[jiraId].instances[0].suite_execution_id;
                        commonService.apiGet("/regression/catalog_test_case_execution_summary_result/" + suiteExecutionId + "/" + jiraId).then(function (data) {
                            $scope.executionDetails[jiraId].summaryResult = data;
                        });
                    });

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

    $scope.overrideSubmitClick = function (testCaseId, instanceIndex, executionId, overrideOption) {
        if(!overrideOption) {
            return commonService.showError("Please select an override option");
        }
        let payload = {};
        payload["execution_id"] = executionId;
        payload["override_result"] = overrideOption;
        let thisTestCaseId = parseInt(testCaseId);
        commonService.apiPost("/regression/update_test_case_execution", payload).then(function (data) {

            $scope.executionDetails[thisTestCaseId].instances[instanceIndex].result = overrideOption;
            $scope.executionDetails[thisTestCaseId].summaryResult = data;
        })

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
