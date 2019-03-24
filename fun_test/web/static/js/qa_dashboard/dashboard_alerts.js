(function (angular) {

'use strict';

function DashboardAlertsController($scope, $http, $window, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        console.log(ctrl);
        $scope.logEntries = [];
        $scope.fetchSessionLogs();
    };

    $scope.fetchSessionLogs = function () {
        let message = "fetchSessionLogs";
        $http.get("/common/get_session_logs").then(function (result) {
            $scope.logEntries = result.data;
        }).catch(function (result) {
            alert("Unable to fetchSessionLogs");
        });
    };

    $scope.showLogToggleClick = function (index) {
        $scope.logEntries[index].show = !$scope.logEntries[index].show;
    };

    $scope.prettyLogs = function (logs) {
        /*return logs.replace("\n", "&#10");*/
        return logs.replace(logs, "<pre>" + logs + "</pre>");

    };


}

    angular.module('qa-dashboard').controller("dashboardAlertsController", DashboardAlertsController);

})(window.angular);
