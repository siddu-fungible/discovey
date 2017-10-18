(function (angular) {
    'use strict';

    function RegressionSuiteDetailTableController($scope, $http, $timeout) {
        let ctrl = this;


        ctrl.$onInit = function () {
            console.log(ctrl);
            /*$scope.suite_executions = null;
            $http.get("/regression/suite_executions").then(function (result) {
                $scope.suite_executions = result.data; // TODO: validate
                let i = 0;

            });*/
        };

    }

    angular.module('qa-dashboard').component('suiteDetailTable', {
        templateUrl: '/static/qa_dashboard/suite_detail_table.html',
        controller: RegressionSuiteDetailTableController,
        bindings: {
            executionId: '<'
        }
    })

})(window.angular);
