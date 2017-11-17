(function (angular) {
    'use strict';

    function SubmitJob($scope, $http, $window, commonAlert) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.scheduleInMinutes = 1;
            $scope.scheduleInMinutesRadio = true;
            $scope.buildUrl = "http://dochub.fungible.local/doc/jenkins/funos/1129/";
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


        $scope.getSchedulingOptions = function(payload) {
            //console.log($scope.selectedSuite);
            if ($scope.schedulingOptions) {

                if($scope.scheduleInMinutesRadio) {
                    if(!$scope.scheduleInMinutes) {
                        commonAlert.showError("Please enter the schedule in minutes value");
                    } else {
                        payload["schedule_in_minutes"] = $scope.scheduleInMinutes;
                        payload["schedule_in_minutes_repeat"] = $scope.scheduleInMinutesRepeat;
                    }


                } else {
                    if(!$scope.scheduleAt) {
                        commonAlert.showError("Please enter the schedule at value");
                        return;
                    } else {
                        payload["schedule_at"] = $scope.scheduleAt;
                        payload["schedule_at_repeat"] = $scope.scheduleAtRepeat;
                    }

                }
            }

            console.log(payload);
            return payload;

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

            if($scope.schedulingOptions) {
                payload = $scope.getSchedulingOptions(payload);
            }
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
