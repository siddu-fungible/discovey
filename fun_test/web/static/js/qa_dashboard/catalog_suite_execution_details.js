(function (angular) {

    'use strict';

    angular.module('qa-dashboard').component('catalogSuiteExecutionDetails', {
        templateUrl: '/static/qa_dashboard/catalog_suite_execution_details.html',
        controller: CatalogSuiteExecutionDetailsController,
        bindings: {
            suiteExecutionId: '@'
        },
    });


    angular.module('qa-dashboard').filter('abs', function() {
        return function(num) { return Math.abs(num); }
    });


    function CatalogSuiteExecutionDetailsController($rootScope, $scope, $http, $window, resultToClass, commonService, $modal) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.series = ['Passed', 'Failed', 'Pending'];

            /* module chart */
            $scope.charting = true;
            $scope.colors = ['#5cb85c', '#d9534f', 'Grey'];
            $scope.overallProgressValues = {};
            $scope.moduleProgressValues = {};
            $scope.updateOverallProgressChartsNow = false;
            $scope.updateModuleProgressChartsNow = false;
            $scope.componentViewDetails = {};

            $scope.fetchModuleComponentMapping().then(function (result) {
                if (result) {
                    $scope.moduleComponentMapping = result;
                    $scope.moduleInfo = {};
                    angular.forEach($scope.moduleComponentMapping, function (info, module) {
                        $scope.moduleInfo[module] = {showingDetails: false, numBlocked: 0};
                    });
                    $scope.fetchCatalogSuiteExecutionDetails(true).then(function () {
                        $scope.fetchBasicIssueAttributes(true).then(function () {
                            $scope.overrideOptions = ["PASSED", "FAILED"];  //TODO
                            $scope.currentView = "components";
                            $scope.testCaseViewInstances = null;
                            $scope.currentTestCaseViewComponent = null;
                            $scope.resetInstanceMetrics();
                            $scope.autoUpdate = true;

                            $scope.updateOverallProgressChartsNow = false;
                            $scope.updateModuleProgressChartsNow = false;
                        });

                    });


                }
            });

        };

        $scope.testClick = function () {
            /*commonService.addLogEntry("CatalogSuiteExecutionDetailsController", "Some details");*/
            /*console.log($scope.updateOverallProgressChartsNow);
            console.log($scope.updateModuleProgressChartsNow);*/
            $scope.editTestCaseClick(124);

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
            let jiraIds = Object.keys($scope.executionDetails.jira_ids);
            /*
            angular.forEach($scope.executionDetails.jira_ids, function (value, key) {
                jiraIds.push(key);
            });*/

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

            return commonService.apiPost("/tcm/basic_issue_attributes", jiraIds, message).then(function (issuesAttributes) {
                if (issuesAttributes) {
                    $scope.recalculateModuleInfo();


                    angular.forEach($scope.executionDetails.jira_ids, function (value, jiraId) {
                        jiraId = parseInt(jiraId);
                        value.summary = issuesAttributes[jiraId].summary;
                        value.components = issuesAttributes[jiraId].components;
                        value.module = issuesAttributes[jiraId].module;

                        if (checkComponents) {
                            $scope._resetComponentViewDetails();
                            let components = value.components;
                            let thisJiraId = jiraId;

                            components.forEach(function (component) {
                                $scope._updateComponentViewDetails(component, thisJiraId);

                            });
                        }
                        attributesFetched += 1;
                        if (attributesFetched === numJiraIds) {
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
                angular.forEach($scope.moduleInfo, function (info, moduleName) {
                    let passedPercentage = (info.numPassed * 100) / (info.numTotal);
                    let failedPercentage = (info.numFailed * 100) / (info.numTotal);
                    let pendingPercentage = ((info.numTotal - info.numPassed - info.numFailed) * 100) / (info.numTotal);
                    $scope.moduleProgressValues[moduleName] = {
                        "Passed": passedPercentage,
                        "Failed": failedPercentage,
                        "Pending": pendingPercentage
                    };

                    $scope.moduleInfo[moduleName].numBlocked = 0;
                    $scope.executionDetails.numBlocked = 0;
                    $scope.moduleComponentMapping[moduleName].forEach(function (component) {
                        if($scope.componentViewDetails.hasOwnProperty(component)) {
                            $scope.moduleInfo[moduleName].numBlocked += $scope.componentViewDetails[component].numBlocked;
                        }
                    });

                    angular.forEach($scope.moduleInfo, function(info, moduleName) {
                        $scope.executionDetails.numBlocked += $scope.moduleInfo[moduleName].numBlocked;
                    });
                });
                $scope.updateModuleProgressChartsNow = true;
            });

        };

        $scope.fetchCatalogSuiteExecutionDetails = function (checkComponents) {
            let message = "fetchCatalogSuiteExecutionDetails";
            $scope.status = "fetchingCatalogExecution";
            return commonService.apiGet('/tcm/catalog_suite_execution_details/' + ctrl.suiteExecutionId, message).then(function (data) {
                $scope.status = "idle";
                $scope.executionDetails = data;
                $scope.executionDetails.numBlocked = 0;
                if ($scope.executionDetails.num_total > 0) {
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
                /*return $scope.fetchBasicIssueAttributes(checkComponents);*/
            });
        };

        $scope._resetComponentViewDetails = function (component) {
            if (!$scope.componentViewDetails.hasOwnProperty(component)) {
                $scope.componentViewDetails[component] = {};
                $scope._resetComponentViewDetails(component);
                $scope.componentViewDetails[component]["jiraIds"] = {};

            }
            $scope.componentViewDetails[component]["numPassed"] = 0;
            $scope.componentViewDetails[component]["numFailed"] = 0;
            $scope.componentViewDetails[component]["numUnknown"] = 0;
            $scope.componentViewDetails[component]["numTotal"] = 0;
            $scope.componentViewDetails[component]["numBlocked"] = 0;
        };

        $scope._updateComponentViewDetails = function (component, jiraId) {
            if (!$scope.componentViewDetails.hasOwnProperty(component)) {
                $scope.componentViewDetails[component] = {};
                $scope._resetComponentViewDetails(component);
                $scope.componentViewDetails[component]["jiraIds"] = {};

            }

            let instances = $scope.executionDetails.jira_ids[jiraId].instances;
            let numPassed = 0;
            let numFailed = 0;
            let numUnknown = 0;
            let numTotal = 0;
            let allBugs = 0;
            let instanceBlockerCount = 0;
            instances.forEach(function (instance) {


                instance.bugs = angular.fromJson(instance.bugs);
                allBugs += instance.bugs.length;
                instance.bugs.forEach(function (bug) {
                    if (bug.blocker) {
                        instanceBlockerCount += 1;
                    }
                });

                numTotal += 1;
                if (instance.result === "PASSED") {
                    numPassed += 1;
                }
                if (instance.result === "FAILED") {
                    numFailed += 1;
                }
                if (instance.result === "UNKNOWN") {
                    numUnknown += 1;
                }
            });
            $scope.componentViewDetails[component]["jiraIds"][jiraId] = {
                "instances": $scope.executionDetails.jira_ids[jiraId].instances,
                allBugs: allBugs,
                blockerCount: instanceBlockerCount,
                summary: $scope.executionDetails.jira_ids[jiraId].summary,
                summaryResult: $scope.executionDetails.jira_ids[jiraId].summaryResult
            };

            if(instanceBlockerCount) {
                $scope.componentViewDetails[component].numBlocked += 1;
            }
            $scope.componentViewDetails[component]["numPassed"] += numPassed;
            $scope.componentViewDetails[component]["numFailed"] += numFailed;
            $scope.componentViewDetails[component]["numUnknown"] += numUnknown;
            $scope.componentViewDetails[component]["numTotal"] += numTotal;


        };

        $scope.overrideSubmitClick = function (testCaseId, instanceIndex, executionId, overrideOption) {
            if (!overrideOption) {
                return commonService.showError("Please select an override option");
            }
            let payload = {};
            payload["execution_id"] = executionId;
            payload["override_result"] = overrideOption;
            let thisTestCaseId = parseInt(testCaseId);
            commonService.apiPost("/regression/update_test_case_execution", payload).then(function (data) {
                $scope.fetchCatalogSuiteExecutionDetails(true).then(function () {
                    $scope.fetchBasicIssueAttributes(false).then(function () {
                        $scope.executionDetails.jira_ids[thisTestCaseId].instances[instanceIndex].result = overrideOption;
                        $scope.executionDetails.jira_ids[thisTestCaseId].summaryResult = data;
                        let components = $scope.executionDetails.jira_ids[thisTestCaseId].components;
                        components.forEach(function (component) {
                            $scope._resetComponentViewDetails(component);
                            angular.forEach($scope.componentViewDetails[component].jiraIds, function (info, thisJiraId) {
                                $scope._updateComponentViewDetails(component, thisJiraId);
                            });
                        });
                    });

                });

                /*$scope.recalculateModuleInfo();*/
                /*$scope.fetchCatalogSuiteExecutionDetails(false);*/
            })

        };

        $scope.moduleDetailsClick = function (component) {
            console.log(component);
            $scope.testCaseViewInstances = $scope.componentViewDetails[component].jiraIds;
            $scope.currentTestCaseViewComponent = component;
        };

        $scope.testCaseViewInstancesDetailsClick = function (jiraId) {
            if (!$scope.testCaseViewInstances[jiraId].hasOwnProperty("showingDetails")) {
                $scope.testCaseViewInstances[jiraId].showingDetails = false;
            }
            $scope.testCaseViewInstances[jiraId].showingDetails = !$scope.testCaseViewInstances[jiraId].showingDetails;
        };

        function EditTestCaseController($scope, item, dialog) {

            $scope.item = item;

            $scope.save = function () {
                dialog.close($scope.item);
            };

            $scope.close = function () {
                dialog.close(undefined);
            };
        }

        $scope.editTestCaseClick = function (jiraId, instance) {
            $modal.open({
                templateUrl: "/static/qa_dashboard/edit_test_case.html",
                controller: ['$modalInstance', '$scope', 'commonService', 'jiraId', 'instance', EditTestCasesController],
                resolve: {
                    jiraId: function () {
                        return jiraId;
                    },
                    instance: function () {
                        return instance;
                    }

                }
            }).result.then(function (res) {

                $scope.fetchCatalogSuiteExecutionDetails(true).then(function () {
                    $scope.fetchBasicIssueAttributes(true).then(function () {
                        let components = $scope.executionDetails.jira_ids[jiraId].components;
                        components.forEach(function (component) {
                            $scope._resetComponentViewDetails(component);
                            angular.forEach($scope.componentViewDetails[component].jiraIds, function (info, thisJiraId) {
                                $scope._updateComponentViewDetails(component, thisJiraId);
                            });
                        });
                    });
                });

                /*$scope.recalculateModuleInfo();*/
            }, function () {

            });


            $scope.toJson = function (bugsString) {
                return angular.fromJson(bugsString);
            };
        }
    }

    function EditTestCasesController($modalInstance, $scope, commonService, jiraId, instance) {
        let ctrl = this;
        $scope.jiraId = jiraId;
        $scope.executionId = instance.execution_id;
        /*
        $scope.bugs = [
            {"id": 123, "summary": "Fetching from JIRA...", "blocker": false},
            {"id": 124, "summary": "Fetching from JIRA...", "blocker": true},

        ];*/
        $scope.bugs = angular.copy(instance.bugs);

        ctrl.$onInit = function () {
            console.log(jiraId);
        };

        $scope.test = function () {
            console.log($scope.jiraId);
        };

        $scope.submit = function () {
            console.log($scope.bugs);
            // Update test-case execution

            let payload = {};
            payload["execution_id"] = $scope.executionId;
            payload["bugs"] = JSON.stringify($scope.bugs);
            commonService.apiPost('/regression/update_test_case_execution', payload).then(function (data) {
                instance.bugs = $scope.bugs;
                $modalInstance.close();
            });

        };

        $scope.addBugClick = function () {
            if ($scope.addBug) {
                $scope.bugs.push({"id": $scope.addBug, "summary": "TBD", "blocker": false});
            }
        };

        $scope.removeClick = function (index) {
            if (confirm("Are you sure you want to remove " + $scope.bugs[index].id + " ?")) {
                $scope.bugs.splice(index, 1)
            }
        };


        /*
        function deletePerson() {
            people.splice(people.indexOf(person), 1);
            $modalInstance.close();
        }*/
    }

})(window.angular);
