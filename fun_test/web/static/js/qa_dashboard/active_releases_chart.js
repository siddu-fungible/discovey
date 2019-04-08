'use strict';


function ActiveReleasesController($scope, $timeout, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.charting = true;
        $scope.colors = ['#5cb85c', '#d9534f', 'purple', 'Grey'];

        $scope.releaseProgressValues = {};
        $scope.series = ["Passed", "Failed", "Blocked", "Pending"];
        $scope.fetchActiveReleases();
        $scope.chartTitle = "Active releases";
        $scope.yAxisTitle = "Percentage";
    };

    $scope.fetchActiveReleases = function () {
        commonService.apiGet('/tcm/active_releases', "fetchActiveReleases").then(function(active_releases){

            active_releases.forEach(function (instance) {
                let suiteExecutionId = instance.fields.suite_execution_id;
                $scope.status = "Fetching Info from JIRA...";
                $scope.releaseProgressValues = {};
                commonService.apiGet("/tcm/catalog_suite_execution_details_with_jira/" + suiteExecutionId).then(function (data) {
                    $scope.status = "idle";
                    let thisInstance = instance;
                    thisInstance.fields.numPassed = 0;
                    thisInstance.fields.numFailed = 0;
                    thisInstance.fields.numTotal = 0;
                    thisInstance.fields.numBlocked = 0;
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
                    $scope.releaseProgressValues[thisInstance.fields.instance_name] = {
                        "Passed": (thisInstance.fields.numPassed * 100)/thisInstance.fields.numTotal,
                        "Failed": (thisInstance.fields.numFailed * 100)/thisInstance.fields.numTotal,
                        "Blocked": (thisInstance.fields.numBlocked * 100)/thisInstance.fields.numTotal,
                        "Pending": ((thisInstance.fields.numTotal - thisInstance.fields.numFailed - thisInstance.fields.numBlocked - thisInstance.fields.numPassed)  * 100)/thisInstance.fields.numTotal,
                        "Link": "/tcm/catalog_suite_execution_details_page/" + suiteExecutionId
                    };
                    let i = 0;


                });
            });



        });
    }
}

/*let activeReleasesComponent = {"name": "activeReleases", "info": activeReleasesInfo};*/

angular.module('qa-dashboard').component("activeReleases", {
    template: ' <div class="panel panel-primary card" style="padding: inherit">\n' +
    '               <div class="panel-heading">Active releases</div>\n' +
    '                   <div class="panel-body"> '+
    '                       <fun-spinner-status status="status" hide-on-idle="true"></fun-spinner-status>\n' +
    '                       <div ng-if="releaseProgressValues" >\n' +
    '                           <fun-chart values="releaseProgressValues" colors="colors" width="400" height="400" title="chartTitle"\n' +
    '                                chart-type="vertical_colored_bar_chart" yaxis-title="yAxisTitle"\n' +
    '                               series="series" charting="charting"></fun-chart>\n' +
    '                       </div>\n' +
    '                   </div>\n' +
    '               </div>\n' +
    '            </div>',

    controller: ActiveReleasesController
});
