(function (angular) {

'use strict';

function CatalogSuiteExecutionDetailsController($rootScope, $scope, $http, $window, resultToClass, commonService) {
    let ctrl = this;
    console.log($rootScope.logEntries);

    ctrl.$onInit = function () {
        $scope.series = ['Passed', 'Failed', 'Pending'];

        /* module chart */
        $scope.charting = true;
        $scope.colors = ['#5cb85c', '#d9534f', 'Grey'];
        $scope.updateOverallProgressChartsNow = false;
        $scope.updateModuleProgressChartsNow = false;
        $scope.fetchModuleComponentMapping().then(function (result) {
            if(result) {
                $scope.moduleComponentMapping = result;
                $scope.moduleInfo = {};
                angular.forEach($scope.moduleComponentMapping, function (info, module) {
                    $scope.moduleInfo[module] = {showingDetails: false};
                });
                $scope.fetchCatalogSuiteExecutionDetails(true);
                $scope.overrideOptions = ["PASSED", "FAILED"];  //TODO
                $scope.currentView = "components";
                $scope.componentViewDetails = {};
                $scope.testCaseViewInstances = null;
                $scope.currentTestCaseViewComponent = null;
                $scope.resetInstanceMetrics();
                $scope.autoUpdate = true;
                $scope.overallProgressValues = {};
                $scope.moduleProgressValues = {};
                $scope.updateOverallProgressChartsNow = false;
                $scope.updateModuleProgressChartsNow = false;

            }
        });

    };

    $scope.testClick = function () {
        /*commonService.addLogEntry("CatalogSuiteExecutionDetailsController", "Some details");*/
        console.log($scope.updateOverallProgressChartsNow);
                console.log($scope.updateModuleProgressChartsNow);

    };

    $scope.moduleShowDetailsClick = function (module) {
        $scope.moduleInfo[module].showingDetails = !$scope.moduleInfo[module].showingDetails;
    };

    $scope.resultToClass = function (result) {
        return resultToClass(result);
    };

    $scope.getComponentInfo = function (component) {
        return $scope.componentViewDetails[component];
    };

    $scope.resetInstanceMetrics = function () {
        $scope.instanceMetrics = {};
    };

    $scope.fetchInstanceMetrics = function () {
        commonService.apiGet('/tcm/instance_metrics/' + ctrl.suiteExecutionId).then(function (data) {

        });
    };

    $scope.fetchBasicIssueAttributes = function (checkComponents) {
        let message = "fetchBasicIssueAttributes";
        let jiraIds = [];
        angular.forEach($scope.executionDetails.jira_ids, function (value, key) {
            jiraIds.push(key);
        });

        let suiteExecutionId = $scope.executionDetails.suite_execution_id;
        let payload = {};
        payload["suite_execution_id"] = suiteExecutionId;
        payload["jira_ids"] = jiraIds;
        $scope.status = "fetchingJira";
        commonService.apiPost('/regression/catalog_test_case_execution_summary_result_multiple_jiras', payload).then(function (summary) {
            angular.forEach(summary, function (value, key) {
                $scope.executionDetails.jira_ids[key].summaryResult = value;
            });
        });

        let numJiraIds = jiraIds.length;
        let attributesFetched = 0;
        commonService.apiPost("/tcm/basic_issue_attributes", jiraIds, message).then(function (issuesAttributes) {
            if(issuesAttributes) {
                $scope.recalculateModuleInfo();

                angular.forEach($scope.executionDetails.jira_ids, function (value, jiraId) {
                    jiraId = parseInt(jiraId);
                    value.summary = issuesAttributes[jiraId].summary;
                    value.components = issuesAttributes[jiraId].components;
                    value.module = issuesAttributes[jiraId].module;

                    if(checkComponents) {
                        $scope._resetComponentViewDetails();
                        let components = value.components;
                        let thisJiraId = jiraId;

                        components.forEach(function (component) {
                            $scope._updateComponentViewDetails(component, thisJiraId);

                        });
                    }
                    attributesFetched += 1;
                    if(attributesFetched === numJiraIds) {
                        /*$scope.status = "idle";*/
                    }
                });

            }
        });
    };

    $scope.fetchModuleComponentMapping = function () {
        let message = "fetchModuleComponentMapping";
        return commonService.apiGet('/tcm/module_component_mapping', message).then(function (data) {
            return data;
        }).catch(function (result) {
            return null;
        });
    };

    $scope.recalculateModuleInfo = function () {
        $scope.status = "fetchingJira";
        commonService.apiGet('/tcm/catalog_suite_execution_details_with_jira/' + ctrl.suiteExecutionId).then(function (data) {
            $scope.status = "idle";
            $scope.moduleInfo = data.module_info;
            angular.forEach($scope.moduleInfo, function(info, moduleName) {
                let passedPercentage = (info.numPassed * 100)/(info.numTotal);
                let failedPercentage = (info.numFailed * 100)/(info.numTotal);
                let pendingPercentage = ((info.numTotal - info.numPassed - info.numFailed) * 100)/(info.numTotal);
                $scope.moduleProgressValues[moduleName] = {"Passed": passedPercentage, "Failed": failedPercentage, "Pending": pendingPercentage};

            });
            $scope.updateModuleProgressChartsNow = true;
        });

    };

    $scope.fetchCatalogSuiteExecutionDetails = function (checkComponents) {
        let message = "fetchCatalogSuiteExecutionDetails";
        $scope.status = "fetchingCatalogExecution";
        $http.get('/tcm/catalog_suite_execution_details/' + ctrl.suiteExecutionId).then(function (result) {
            $scope.status = "idle";
            if (!commonService.validateApiResult(result, message)) {
                return;
            }
            $scope.executionDetails = result["data"]["data"];
            if($scope.executionDetails.num_total > 0) {
                $scope.executionDetails.passedPercentage = $scope.executionDetails.num_passed * 100 / $scope.executionDetails.num_total;
                $scope.executionDetails.failedPercentage = $scope.executionDetails.num_failed * 100 / $scope.executionDetails.num_total;
                $scope.executionDetails.pendingPercentage = ($scope.executionDetails.num_total - ($scope.executionDetails.num_passed + $scope.executionDetails.num_failed)) * 100 / $scope.executionDetails.num_total;
                $scope.overallProgressValues["Passed"] = $scope.executionDetails.passedPercentage;
                $scope.overallProgressValues["Failed"] = $scope.executionDetails.failedPercentage;
                $scope.overallProgressValues["Pending"] = $scope.executionDetails.pendingPercentage;
                $scope.updateOverallProgressChartsNow = true;
                /*$scope.$digest();*/
            }

            // Fetch basic issue attributes
            return $scope.fetchBasicIssueAttributes(checkComponents);
        }).catch(function (result) {
            return commonService.showHttpError(message, result);
        });
    };

    $scope._resetComponentViewDetails = function (component) {
        if(!$scope.componentViewDetails.hasOwnProperty(component)) {
            $scope.componentViewDetails[component] = {};
            $scope._resetComponentViewDetails(component);
            $scope.componentViewDetails[component]["jiraIds"] = {};

        }
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

        let instances = $scope.executionDetails.jira_ids[jiraId].instances;
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
        $scope.componentViewDetails[component]["jiraIds"][jiraId] = {"instances": $scope.executionDetails.jira_ids[jiraId].instances,
            summary: $scope.executionDetails.jira_ids[jiraId].summary,
        summaryResult: $scope.executionDetails.jira_ids[jiraId].summaryResult};
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

            $scope.executionDetails.jira_ids[thisTestCaseId].instances[instanceIndex].result = overrideOption;
            $scope.executionDetails.jira_ids[thisTestCaseId].summaryResult = data;
            let components = $scope.executionDetails.jira_ids[thisTestCaseId].components;
            components.forEach(function(component) {
                $scope._resetComponentViewDetails(component);
                angular.forEach($scope.componentViewDetails[component].jiraIds, function (info, thisJiraId) {
                    $scope._updateComponentViewDetails(component, thisJiraId);
                });
            });
            /*$scope.recalculateModuleInfo();*/
            $scope.fetchCatalogSuiteExecutionDetails(false);
        })

    };

    $scope.moduleDetailsClick = function (component) {
        console.log(component);
        $scope.testCaseViewInstances = $scope.componentViewDetails[component].jiraIds;
        $scope.currentTestCaseViewComponent = component;
    };

    $scope.testCaseViewInstancesDetailsClick = function (jiraId) {
        if(!$scope.testCaseViewInstances[jiraId].hasOwnProperty("showingDetails")) {
            $scope.testCaseViewInstances[jiraId].showingDetails = false;
        }
        $scope.testCaseViewInstances[jiraId].showingDetails = !$scope.testCaseViewInstances[jiraId].showingDetails;
    };

}

angular.module('qa-dashboard').component('catalogSuiteExecutionDetails', {
    templateUrl: '/static/qa_dashboard/catalog_suite_execution_details.html',
    controller: CatalogSuiteExecutionDetailsController,
    bindings: {
        suiteExecutionId: '@'
    },
});
})(window.angular);
