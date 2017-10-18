(function (angular) {
    'use strict';

    function RegressionTableController($scope, $http, $timeout) {
        let ctrl = this;


        ctrl.$onInit = function () {
            console.log(ctrl);
            $scope.suite_executions = null;
            $http.get("/regression/suite_executions").then(function (result) {
                $scope.suite_executions = result.data; // TODO: validate
                let i = 0;

            });
        };

        $scope.testCaseLength = function(testCases) {
            return angular.fromJson(testCases).length;
        };

        $scope.getResultButtonClass = function (result) {
            let buttonClass = "btn-default";
            if(result === "FAILED") {
                buttonClass = "btn-danger";
            } else if(result === "PASSED") {
                buttonClass = "btn-success"
            } else if(result === "SKIPPED") {
                buttonClass = "btn-warning"
            } else if(result === "NOT_RUN") {
                buttonClass = "btn-info"
            }
            return buttonClass;
        };


    }

    angular.module('qa-dashboard').component('regressionTable', {
        templateUrl: '/static/qa_dashboard/regression_table.html',
        controller: RegressionTableController,
        bindings: {
            f1: '='
        }
    })

})(window.angular);
