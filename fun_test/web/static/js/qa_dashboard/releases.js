(function (angular) {
    'use strict';

    function ReleasesController($scope, $http, $window, $timeout, commonService) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.status = "idle";
            $scope.fetchReleases();
        };

        $scope.activeReleaseClick = function (suiteExecutionId, event) {
            let active = 0;
            if (event.target.checked) {
                active = 1;
            }

            commonService.apiGet('/tcm/set_active_release/' + suiteExecutionId + "/" + active, "activeReleaseClick").then(function (data) {

            });
        };

        $scope.fetchReleases = function () {
            $scope.status = "Fetching Releases...";

            commonService.apiGet('/tcm/releases', "fetchReleases").then(function (data) {
                $scope.catalogExecutionSummary = data;
                $scope.catalogExecutionSummary.forEach(function (instance) {
                    let suiteExecutionId = instance.fields.suite_execution_id;
                    $scope.status = "Fetching Info from JIRA...";

                    commonService.apiGet("/tcm/catalog_suite_execution_details_with_jira/" + suiteExecutionId).then(function (data) {
                        $scope.status = "idle";
                        let thisInstance = instance;
                        thisInstance.fields.numPassed = 0;
                        thisInstance.fields.numFailed = 0;
                        thisInstance.fields.numBlocked = 0;
                        thisInstance.fields.numTotal = 0;
                        angular.forEach(data.jira_ids, function (info, jiraId) {
                            info.instances.forEach(function (instance) {
                                thisInstance.fields.numTotal += 1;
                                if (instance.result === "PASSED") {
                                    thisInstance.fields.numPassed += 1;
                                }
                                if (instance.result === "FAILED") {
                                    thisInstance.fields.numFailed += 1;
                                }
                                if (instance.result === "BLOCKED") {
                                    thisInstance.fields.numBlocked += 1;
                                }

                            });
                        });
                    });
                });

            });
        };
    }

    angular.module('qa-dashboard').controller("releasesController", ReleasesController);

})(window.angular);
