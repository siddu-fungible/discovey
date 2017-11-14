(function (angular) {
    'use strict';

    function SubmitJob($scope, $http, $window, commonAlert) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.scheduleInMinutesRadio = true;
            $scope.buildUrl = "http://dochub.fungible.local/doc/jenkins/funos/latest/";
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


        $scope.testClick = function() {
            /*console.log($scope.scheduleAt);
            console.log($scope.scheduleInMinutes);
            console.log($scope.scheduleInRepeat);
            console.log($scope.scheduleAtRepeat);*/
            console.log($scope.scheduleInMinutesRadio);
            console.log($scope.scheduleAtRadio);
            console.log($scope.scheduleRadio);

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
