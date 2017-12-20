(function (angular) {

'use strict';

function CatalogSuiteExecutionDetailsController($scope, $http, $window, resultToClass, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.fetchCatalogSuiteExecutionDetails();
        $scope.overrideOptions = ["PASSED", "FAILED"];  //TODO
        $scope.currentView = "components";
        $scope.componentViewDetails = {};
        $scope.testCaseViewInstances = null;
        $scope.currentTestCaseViewComponent = null;
        $scope.status = "idle";
    };

    $scope.resultToClass = function (result) {
        return resultToClass(result);
    };

    $scope.test = function () {
        //console.log($scope.currentView);
        console.log($scope.componentViewDetails);
    };

    $scope.fetchBasicIssueAttributes = function () {
        let message = "fetchBasicIssueAttributes";
        let jiraIds = [];
        angular.forEach($scope.executionDetails, function (value, key) {
            jiraIds.push(key);
        });

        $scope.status = "fetchingJira";
        commonService.apiPost("/tcm/basic_issue_attributes", jiraIds, message).then(function (issuesAttributes) {
            $scope.status = null;
            let summaryResults = 0;
            if(issuesAttributes) {
                angular.forEach($scope.executionDetails, function (value, key) {
                    value.summary = issuesAttributes[parseInt(key)].summary;
                    value.components = issuesAttributes[parseInt(key)].components;
                    let jiraId = null;
                    if(Object.keys($scope.executionDetails)) {

                    }
                    let numJiraIds = jiraIds.length;
                    jiraIds.forEach(function (jiraId) {
                        let suiteExecutionId = $scope.executionDetails[jiraId].instances[0].suite_execution_id;
                        commonService.apiGet("/regression/catalog_test_case_execution_summary_result/" + suiteExecutionId + "/" + jiraId).then(function (data) {
                            $scope.executionDetails[jiraId].summaryResult = data;
                            summaryResults += 1;

                            if(summaryResults === numJiraIds) {
                                angular.forEach(issuesAttributes, function (info, jiraId) {
                                    let components = info.components;
                                    let thisJiraId = jiraId;
                                    components.forEach(function (component) {
                                        $scope._updateComponentViewDetails(component, thisJiraId);

                                    });
                                });
                            }
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

    $scope._resetComponentViewDetails = function (component) {
        $scope.componentViewDetails[component]["numPassed"] = 0;
        $scope.componentViewDetails[component]["numFailed"] = 0;
        $scope.componentViewDetails[component]["numUnknown"] = 0;
        $scope.componentViewDetails[component]["numTotal"] = 0;
    };

    $scope._updateComponentViewDetails = function (component, jiraId) {
        if(!$scope.componentViewDetails.hasOwnProperty(component)) {
            $scope.componentViewDetails[component] = {};
            $scope._resetComponentViewDetails(component);
            $scope.componentViewDetails[component]["jiraIds"] = {};

        }

        let instances = $scope.executionDetails[jiraId].instances;
        let numPassed = 0;
        let numFailed = 0;
        let numUnknown = 0;
        let numTotal = 0;
        instances.forEach(function (instance) {
            numTotal += 1;
            if(instance.result === "PASSED") {
                numPassed += 1;
            }
            if(instance.result === "FAILED") {
                numFailed += 1;
            }
            if(instance.result === "UNKNOWN") {
                numUnknown += 1;
            }
        });
        $scope.componentViewDetails[component]["jiraIds"][jiraId] = {"instances": $scope.executionDetails[jiraId].instances,
            summary: $scope.executionDetails[jiraId].summary,
        summaryResult: $scope.executionDetails[jiraId].summaryResult};
        $scope.componentViewDetails[component]["numPassed"] += numPassed;
        $scope.componentViewDetails[component]["numFailed"] += numFailed;
        $scope.componentViewDetails[component]["numUnknown"] += numUnknown;
        $scope.componentViewDetails[component]["numTotal"] += numTotal;

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
            let components = $scope.executionDetails[thisTestCaseId].components;
            components.forEach(function(component) {
                $scope._resetComponentViewDetails(component);
                angular.forEach($scope.componentViewDetails[component].jiraIds, function (info, thisJiraId) {
                    $scope._updateComponentViewDetails(component, thisJiraId);
                });
            });
        })

    };

    $scope.totalClick = function (component) {
        console.log(component);
        $scope.testCaseViewInstances = $scope.componentViewDetails[component].jiraIds;
        $scope.currentTestCaseViewComponent = component;
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
