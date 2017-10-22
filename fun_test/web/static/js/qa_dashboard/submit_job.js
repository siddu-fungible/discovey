(function (angular) {
    'use strict';

    function SubmitJob($scope, $http, $window) {
        let ctrl = this;

        ctrl.$onInit = function () {
            console.log(ctrl);
            $scope.selectedSuite = null;
            $scope.selectedInfo = null;
            $scope.jobId = null;
            $http.get("/regression/suites").then(function(result) {
                $scope.suitesInfo = result.data;
            });
        };

        $scope.changedValue = function(selectedSuite) {
            $scope.selectedInfo = $scope.suitesInfo[selectedSuite];
        };


        $scope.submitClick = function () {
            console.log($scope.selectedSuite);
            $scope.jobId = null;
            let payload = {};
            payload["suite_path"] = $scope.selectedSuite;
            $http.post('/regression/submit_job', payload).then(function(result){
                $scope.jobId = parseInt(result.data);
                $window.location.href = "/regression/suite_detail/" + $scope.jobId;

            });
        }

    }

    angular.module('qa-dashboard').component('submitJob', {
        templateUrl: '/static/qa_dashboard/submit_job.html',
        controller: SubmitJob,
        bindings: {
        }
    })

})(window.angular);
