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

        $scope.setComponentModuleMapping = function () {
            $scope.componentModuleMapping = {};
            angular.forEach($scope.moduleComponentMapping, function(components, module) {
                components.forEach(function (component) {
                    $scope.componentModuleMapping[component] = module;
                });
            });
            let i = 0;
        };

        ctrl.$onInit = function () {
            $scope.series = ['Passed', 'Failed', 'Blocked', 'Pending'];

            /* module chart */
            $scope.charting = true;
            $scope.colors = ['#5cb85c', '#d9534f', 'Purple', 'Grey'];
            $scope.overallProgressValues = {};
            $scope.moduleProgressValues = {};
            $scope.updateOverallProgressChartsNow = false;
            $scope.updateModuleProgressChartsNow = false;
            $scope.componentViewDetails = {};
            $scope.lastTestCaseViewList = [];
            $scope.selectAllTestCases = false;

            $scope.overallProgressTitle = "Overall progress";
            $scope.moduleProgressTitle = "Module progress";
            $scope.moduleProgressYaxisTitle = "Percentage";

            $scope.fetchModuleComponentMapping().then(function (result) {
                if (result) {
                    $scope.moduleComponentMapping = result;
                    $scope.setComponentModuleMapping();

                    $scope.moduleInfo = {};
                    angular.forEach($scope.moduleComponentMapping, function (info, module) {
                        $scope.moduleInfo[module] = {showingDetails: false, numBlocked: 0};
                    });
                    $scope.fetchCatalogSuiteExecutionDetails(true).then(function () {
                        $scope.fetchBasicIssueAttributes(true).then(function () {
                            $scope.overrideOptions = ["PASSED", "FAILED", "NOT_RUN"];  //TODO
                            $scope.currentView = "components";
                            //$scope.currentView = "all";

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
            /*$scope.editTestCaseClick(124);*/
            console.log($scope.selectAllTestCases);

        };

        $scope.moduleShowDetailsClick = function (module) {
            $scope.moduleInfo[module].showingDetails = !$scope.moduleInfo[module].showingDetails;
        };

        $scope.getLabel = (text) => {
            let title = "U";
            let labelClass = "";
            let briefText = "";
            if(text.includes("Passed")) {
                briefText = "P";
                labelClass = "label-success";
            } else if(text.includes("Failed")) {
                briefText = "F";
                labelClass = "label-danger";
            } else if(text.includes("Pending")) {
                briefText = "Pn";
                labelClass = "label-default"
            } else if(text.includes("Blocked")) {
                labelClass = "label-blocked";
                briefText = "B"
            }
            if(text.includes("%")) {
                briefText += "%";
            }
            let s = '<label data-placement="top" data-toggle="tooltip" title="' + text + '" class="label ';
            s += labelClass + '">' + briefText + "</label>";
            return s;
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
                    let pendingPercentage = ((info.numTotal - info.numPassed - info.numFailed) * 100) / (info.numTotal);


                    $scope.moduleInfo[moduleName].numBlocked = 0;
                    $scope.executionDetails.numBlocked = 0;
                    let blockedSetOfTcs = new Set();
                    $scope.moduleComponentMapping[moduleName].forEach(function (component) {
                        if($scope.componentViewDetails.hasOwnProperty(component)) {
                            /*$scope.moduleInfo[moduleName].numBlocked += $scope.componentViewDetails[component].numBlocked;*/
                            angular.forEach($scope.componentViewDetails[component].jiraIds, function (info, jiraId) {
                                if(info.blockerCount) {
                                    blockedSetOfTcs.add(jiraId);
                                }
                            });
                        }
                    });
                    $scope.moduleInfo[moduleName].numBlocked = blockedSetOfTcs.size;
                    let moduleBlockedPercentage = $scope.moduleInfo[moduleName].numBlocked * 100/$scope.moduleInfo[moduleName].numTotal;
                    let moduleFailedPercentage = $scope.moduleInfo[moduleName].numFailed * 100 / (info.numTotal);
                    moduleFailedPercentage = Math.abs(moduleFailedPercentage - moduleBlockedPercentage);

                    $scope.moduleProgressValues[moduleName] = {
                        "Passed": passedPercentage,
                        "Failed": moduleFailedPercentage,
                        "Blocked": moduleBlockedPercentage,
                        "Pending": pendingPercentage,
                    };

                    angular.forEach($scope.moduleInfo, function(info, moduleName) {
                        $scope.executionDetails.numBlocked += $scope.moduleInfo[moduleName].numBlocked;
                    });
                    $scope.executionDetails.blockedPercentage = $scope.executionDetails.numBlocked * 100/$scope.executionDetails.num_total;
                    $scope.overallProgressValues["Passed"] = $scope.executionDetails.passedPercentage;
                    $scope.overallProgressValues["Failed"] = Math.abs($scope.executionDetails.failedPercentage - $scope.executionDetails.blockedPercentage)
                    $scope.overallProgressValues["Pending"] = $scope.executionDetails.pendingPercentage;
                    $scope.overallProgressValues["Blocked"] = $scope.executionDetails.blockedPercentage;
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
                    $scope.executionDetails.failedPercentage = Math.abs($scope.executionDetails.num_failed - $scope.executionDetails.numBlocked) * 100/$scope.executionDetails.num_total;
                    $scope.executionDetails.pendingPercentage = ($scope.executionDetails.num_total - ($scope.executionDetails.num_passed + $scope.executionDetails.num_failed - $scope.executionDetails.numBlocked)) * 100 / $scope.executionDetails.num_total;
                    $scope.executionDetails.blockedPercentage = $scope.executionDetails.numBlocked * 100/$scope.executionDetails.num_total;
                    /*$scope.overallProgressValues["Passed"] = $scope.executionDetails.passedPercentage;
                    $scope.overallProgressValues["Blocked"] = $scope.executionDetails.blockedPercentage;
                    $scope.overallProgressValues["Failed"] = $scope.executionDetails.failedPercentage;
                    $scope.overallProgressValues["Pending"] = $scope.executionDetails.pendingPercentage;*/
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
            if($scope.lastTestCaseViewList.indexOf(jiraId) > -1) {
                $scope.componentViewDetails[component]["jiraIds"][jiraId].show = true;
                Object.assign($scope.testCaseViewInstances, $scope.componentViewDetails[component]["jiraIds"]);
            }

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
            if($scope.executionDetails.jira_ids[testCaseId].instances[instanceIndex].bugs.length) {
                if (overrideOption === "PASSED") {
                    let message = "This instance has bugs on it. Please remove the bugs before setting the result to PASSED";
                    alert(message);
                    return commonService.showError(message);
                }
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

        $scope.componentDetailsClick = function (component) {
            console.log(component);
            $scope.testCaseViewInstances = $scope.componentViewDetails[component].jiraIds;
            $scope.currentTestCaseViewComponent = component;
        };

        $scope.selectAllTestCasesClick = function () {
            console.log($scope.selectAllTestCases);
            angular.forEach($scope.testCaseViewInstances, function(info, jiraId) {
                info.selected = $scope.selectAllTestCases;
            });
        };

        $scope.selectTestCaseClick = function (jiraId) {
            console.log($scope.testCaseViewInstances[jiraId].selected);
        };

        $scope.moduleFilterClick = function(module, filter) {
            $scope.lastTestCaseViewList = [];
            $scope.testCaseViewInstances = {};
            if(filter === "TOTAL") {
                angular.forEach($scope.componentViewDetails, function(info, component) {
                    if(component !== "undefined" && ($scope.componentModuleMapping[component] === module || (module === "ALL"))) {
                        angular.forEach(info.jiraIds, function(innerInfo, jiraId) {
                            innerInfo.show = true;
                            $scope.lastTestCaseViewList.push(jiraId);
                        });
                        Object.assign($scope.testCaseViewInstances, $scope.componentViewDetails[component].jiraIds);
                    }
                });
            } else if(filter === "BLOCKED") {
                angular.forEach($scope.componentViewDetails, function(info, component) {

                    if (component !== "undefined" && ($scope.componentModuleMapping[component] === module || (module === "ALL"))) {
                        angular.forEach(info.jiraIds, function (innerInfo, jiraId) {
                            if (innerInfo.summaryResult === "FAILED" && innerInfo.blockerCount) {
                                innerInfo.show = true;
                                $scope.lastTestCaseViewList.push(jiraId);

                            } else {
                                innerInfo.show = false;
                            }
                        });
                        Object.assign($scope.testCaseViewInstances, info.jiraIds);

                    }
                })
            } else if(filter === "PENDING") {
                angular.forEach($scope.componentViewDetails, function(info, component) {
                    if(component !== "undefined" && ($scope.componentModuleMapping[component] === module || (module === "ALL"))) {
                        angular.forEach(info.jiraIds, function(innerInfo, jiraId) {
                            if(innerInfo.summaryResult !== "PASSED" && innerInfo.summaryResult !== "FAILED") {
                                innerInfo.show = true;
                                $scope.lastTestCaseViewList.push(jiraId);

                            } else {
                                innerInfo.show = false;
                            }
                        });
                        Object.assign($scope.testCaseViewInstances, info.jiraIds);
                    }
                });
            } else {
                angular.forEach($scope.componentViewDetails, function(info, component) {
                    if(component !== "undefined" && ($scope.componentModuleMapping[component] === module || (module === "ALL"))) {
                        angular.forEach(info.jiraIds, function(innerInfo, jiraId) {
                            if(innerInfo.summaryResult === filter) {
                                innerInfo.show = true;
                                $scope.lastTestCaseViewList.push(jiraId);

                            } else {
                                innerInfo.show = false;
                            }
                        });
                        Object.assign($scope.testCaseViewInstances, info.jiraIds);
                    }
                });
            }
        };

        $scope.componentFilterClick = function (component, filter) {
            $scope.lastTestCaseViewList = [];
            $scope.testCaseViewInstances = $scope.componentViewDetails[component].jiraIds;

            if(filter === "TOTAL") {
                angular.forEach($scope.componentViewDetails[component].jiraIds, function(info, jiraId) {
                    info.show = true;
                    $scope.lastTestCaseViewList.push(jiraId);
                });
                $scope.currentTestCaseViewComponent = component;
            } else if(filter === "BLOCKED") {
                angular.forEach($scope.componentViewDetails[component].jiraIds, function(info, jiraId) {
                    if(info.blockerCount) {
                        info.show = true;
                        $scope.lastTestCaseViewList.push(jiraId);
                    } else {
                        info.show = false;
                    }
                });

            } else if(filter === "PENDING") {
                angular.forEach($scope.componentViewDetails[component].jiraIds, function(info, jiraId) {
                    if(info.summaryResult !== "PASSED" && info.summaryResult !== "FAILED") {
                        info.show = true;
                        $scope.lastTestCaseViewList.push(jiraId);

                    } else {
                        info.show = false;
                    }
                });

            } else {
                angular.forEach($scope.componentViewDetails[component].jiraIds, function(info, jiraId) {
                    if(info.summaryResult === filter) {
                        info.show = true;
                        $scope.lastTestCaseViewList.push(jiraId);

                    } else {
                        info.show = false;
                    }
                });
            }
        };

        $scope.testCaseViewInstancesDetailsClick = function (jiraId) {
            if (!$scope.testCaseViewInstances[jiraId].hasOwnProperty("showingDetails")) {
                $scope.testCaseViewInstances[jiraId].showingDetails = false;
            }
            $scope.testCaseViewInstances[jiraId].showingDetails = !$scope.testCaseViewInstances[jiraId].showingDetails;
        };



        $scope.bulkEditTestCaseClick = function () {
            /* Ensure at least one test-case is selected */
            let oneTestCaseSelected = false;
            angular.forEach($scope.testCaseViewInstances, function (info, jiraId) {
                if(info.selected) {
                    oneTestCaseSelected = true;
                }
            });
            if(!oneTestCaseSelected) {
                return commonService.showError("Please select at least one test-case");
            }

            $modal.open({
                templateUrl: "/static/qa_dashboard/bulk_edit_test_case.html",
                controller: ['$modalInstance', '$scope', 'commonService', '$http', 'testCaseViewInstances', BulkEditTestCasesController],
                resolve: {
                    testCaseViewInstances: function () {
                        return $scope.testCaseViewInstances;
                    }
                }
            }).result.then(function () {
                $scope.fetchCatalogSuiteExecutionDetails(true).then(function () {
                    $scope.fetchBasicIssueAttributes(true).then(function () {

                        angular.forEach($scope.testCaseViewInstances, function (info, jiraId) {
                            let components = $scope.executionDetails.jira_ids[jiraId].components;
                            components.forEach(function (component) {
                                $scope._resetComponentViewDetails(component);
                                angular.forEach($scope.componentViewDetails[component].jiraIds, function (info, jiraId) {
                                    $scope._updateComponentViewDetails(component, jiraId);
                                });
                            });
                        })

                    });
                });
            })
        };

        $scope.addTestCasesClick = function () {
            $modal.open({
                templateUrl: "/static/qa_dashboard/add_test_cases.html",
                controller: ['$modalInstance', '$scope', 'commonService', 'suiteExecutionId', 'ownerEmail', AddTestCasesController],
                resolve: {
                    suiteExecutionId: function () {
                        return $scope.executionDetails.suite_execution_id;
                    },
                    ownerEmail: function () {
                        return $scope.executionDetails.owner_email;
                    }
                }}).result.then(function () {

                }, function () {

                })
        };


        $scope.editTestCaseClick = function (jiraId, instance) {
            if(instance.result !== "FAILED") {
                let message = "Unable to edit bugs unless the test-case execution result is marked FAILED";
                alert(message);
                return commonService.showError(message);
            }

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
            }).result.then(function () {

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

    function BulkEditTestCasesController($modalInstance, $scope, commonService, $http, testCaseViewInstances) {
        let ctrl = this;
        $scope.resultOptions = [null, "PASSED", "FAILED"];
        $scope.owners = [{"name": "No change"}];
        $scope.bugs = [];
        $scope.testCaseViewInstances = testCaseViewInstances;

        $scope.fetchOwners = function () {
            $http.get("/regression/engineers").then(function (result) {
                if(!commonService.validateApiResult(result, "Fetch Engineers")) {
                    return;
                }
                let data = result.data.data;
                data.forEach(function (element) {
                    $scope.owners.push({"name": element.fields.short_name, "email": element.fields.email});
                });

            }).catch(function (result) {
                commonService.showHttpError("Unable to fetch owners", result)
            });
        };
        $scope.fetchOwners();

        $scope.submit = function () {
            console.log($scope.selectedResult);
            if($scope.selectedResult) {
                console.log("yes");
            }
            if($scope.bugs.length && ($scope.selectedResult !== "FAILED")) {
                return commonService.showError("Please set the result to FAILED, if you need to add bugs");
            }

            console.log($scope.selectedOwner);
            // Update test-case execution


            $scope.numPostRequests = 0;
            $scope.numPostResponses = 0;

            angular.forEach($scope.testCaseViewInstances, function(info, jiraId) {
                if(info.selected && info.show) {
                    console.log(jiraId);
                    info.instances.forEach(function (instance) {
                        let payload = {};
                        payload["execution_id"] = instance.execution_id;
                        if($scope.bugs) {
                            payload["bugs"] = JSON.stringify($scope.bugs);
                        }
                        if($scope.selectedResult) {
                            payload["override_result"] = $scope.selectedResult;
                        }
                        if($scope.selectedOwner) {
                            payload["owner_email"] = $scope.selectedOwner.email;
                        }
                        $scope.numPostRequests += 1;
                        commonService.apiPost('/regression/update_test_case_execution', payload).then(function (data) {

                            $scope.numPostResponses += 1;
                            if($scope.numPostResponses === $scope.numPostRequests) {
                                $modalInstance.close();
                            }
                        });
                    });
                }
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

    }

    function AddTestCasesController($modalInstance, $scope, commonService, suiteExecutionId, ownerEmail) {
        let ctrl = this;
        $scope.status = "idle";
        $scope.jqlValid = false;
        $scope.validating = false;
        $scope.suiteExecutionId = suiteExecutionId;
        $scope.ownerEmail = ownerEmail;

        $scope.validateClick = function () {
            $scope.validating = true;
            $scope.testCases = null;
            let payload = {};
            payload["jqls"] = [$scope.jql];

            let message = "AddTestCasesController";
            $scope.status = "Fetching JIRA entries";
            $scope.jqlValid = false;
            commonService.apiPost("/tcm/preview_catalog", payload, message).then(function (data) {
                $scope.status = "idle";
                if(data) {
                    $scope.jqlValid = true;
                    $scope.testCases = data.test_cases;
                }
                let i = 0;
            });
        };

        $scope.submit = function () {
            let payload = {};
            payload["suite_execution_id"] = $scope.suiteExecutionId;
            payload["owner_email"] = $scope.ownerEmail;
            payload["test_cases"] = $scope.testCases;
            commonService.apiPost('/tcm/catalog_execution_add_test_cases', payload).then(function (data) {
                $modalInstance.close();
                $window.location.reload();

            });
        };


    }

})(window.angular);
