function SuitesTableController($scope, $http, resultToClass, $window) {
    let ctrl = this;

    $scope.resultToClass = function (result) {
        return resultToClass(result);
    };

    ctrl.$onInit = function () {
        //console.log(ctrl);
        $scope.suite_executions = null;
        $http.get("/regression/suite_executions").then(function (result) {
            $scope.suiteExecutions = result.data; // TODO: validate
            let i = 0;

        });
    };

    $scope.testCaseLength = function (testCases) {
        return angular.fromJson(testCases).length;
    };

    $scope.getSuiteDetail = function (suiteId) {
        console.log(suiteId);
        $window.location.href = "/regression/suite_detail/" + suiteId;
    }

}

angular.module('qa-dashboard')
    .component('suitesTable', {
        templateUrl: '/static/qa_dashboard/suites_table.html',
        controller: SuitesTableController,
        bindings: {}
    });