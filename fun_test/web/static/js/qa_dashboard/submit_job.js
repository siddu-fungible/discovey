(function (angular) {
    'use strict';

    function SubmitJob($scope, $http, $window, commonAlert) {
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


        $scope.submitClick = function (formIsValid) {
            if(!formIsValid) {
               commonAlert.showError("Form is invalid");
               return;
            }
            console.log($scope.selectedSuite);
            $scope.jobId = null;
            let payload = {};
            payload["suite_path"] = $scope.selectedSuite;
            payload["build_url"] = $scope.buildUrl;
            $http.post('/regression/submit_job', payload).then(function(result){
                $scope.jobId = parseInt(result.data);
                $window.location.href = "/regression/suite_detail/" + $scope.jobId;
                commonAlert.showSuccess("Job " + $scope.jobId + " Submitted");
            }).catch(function(result) {
                commonAlert.showError("Unable to submit job");
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
