(function (angular) {
    'use strict';

    function SuiteDetailTableController($scope, $http, $timeout, resultToClass) {
        let ctrl = this;

        $scope.resultToClass = function (result) {
            return resultToClass(result);
        };

        ctrl.$onInit = function () {
            console.log(ctrl);
            $scope.testCaseExecutions = [];
            $http.get("/regression/suite_execution/" + ctrl.executionId).then(function (result) {
                $scope.suiteExecution = result.data; // TODO: validate
                let testCaseExecutionIds = angular.fromJson($scope.suiteExecution.fields.test_case_execution_ids);

                angular.forEach(testCaseExecutionIds, function(testCaseExecutionId) {
                    $http.get('/regression/test_case_execution/' + ctrl.executionId + "/" + testCaseExecutionId).then(function(result){
                        //result.data
                        $scope.testCaseExecutions.push(result.data[0]);

                    })
                });

            });
        };

    }

    angular.module('qa-dashboard').component('suiteDetailTable', {
        templateUrl: '/static/qa_dashboard/suite_detail_table.html',
        controller: SuiteDetailTableController,
        bindings: {
            executionId: '<'
        }
    })

})(window.angular);
