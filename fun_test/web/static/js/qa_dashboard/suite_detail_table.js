(function (angular) {
    'use strict';

    function SuiteDetailTableController($scope, $http, $timeout, resultToClass, $window, trimTime) {
        let ctrl = this;

        $scope.resultToClass = function (result) {
            return resultToClass(result);
        };

        ctrl.$onInit = function () {
            $scope.logDir = null;
            $scope.CONSOLE_LOG_EXTENSION = ".logs.txt";  //TIED to scheduler_helper.py  TODO
            $scope.HTML_LOG_EXTENSION = ".html";         //TIED to scheduler_helper.py  TODO


            if(!$scope.logDir) {
                $http.get("/regression/log_path").then(function (result) {
                    $scope.logDir = result.data;
                }).catch(function () {
                    $scope.logDir = "/static/logs/s_"
                });
            }

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

        let _getFlatPath = function (path) {

            let httpPath = $scope.logDir + ctrl.executionId;
            let parts = path.split("/");
            let flat = path;
            let numParts = parts.length;
            if (numParts > 2) {
                flat = parts[numParts - 2] + "_" + parts[numParts - 1];
            }
            return httpPath + "/" + flat.replace(/^\//g, '');
        };

        $scope.getHtmlLogPath = function (path) {
            return _getFlatPath(path) + $scope.HTML_LOG_EXTENSION;
        };

        $scope.getConsoleLogPath = function (path) {
            return _getFlatPath(path) + $scope.CONSOLE_LOG_EXTENSION;
        };

        $scope.trimTime = function (t) {
            return trimTime(t);
        };

        $scope.rerunClick = function(suiteExecutionId, testCaseExecutionId, scriptPath) {
            let payload = {};
            payload["suite_execution_id"] = suiteExecutionId;
            payload["test_case_execution_id"] = testCaseExecutionId;
            payload["script_path"] = scriptPath;
            $http.post("/regression/test_case_re_run", payload).then(function (result) {
                let jobId = parseInt(result.data);
                $window.location.href = "/regression/suite_detail/" + jobId;
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
