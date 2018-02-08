(function (angular) {
    'use strict';

    function SubmitJob($scope, $http, $window, commonService) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.scheduleInMinutes = 1;
            $scope.scheduleInMinutesRadio = true;
            $scope.buildUrl = "http://dochub.fungible.local/doc/jenkins/funos/latest/";
            console.log(ctrl);
            $scope.selectedSuite = null;
            $scope.selectedInfo = null;
            $scope.jobId = null;
            $http.get("/regression/suites").then(function(result) {
                $scope.suitesInfo = result.data;
            });
            ctrl.selectedTags = [];
            $scope.tags = [];
            $scope.fetchTags();
        };

        $scope.fetchTags = function() {
            $http.get('/regression/tags').then(function(result){
                let data = result.data;
                data.forEach(function(item){
                    $scope.tags.push({name: item.fields.tag});
                });

            }).catch(function(result) {
                commonService.showError("Unable to fetch tags");
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
                        commonService.showError("Please enter the schedule in minutes value");
                    } else {
                        payload["schedule_in_minutes"] = $scope.scheduleInMinutes;
                        payload["schedule_in_minutes_repeat"] = $scope.scheduleInMinutesRepeat;
                    }


                } else {
                    if(!$scope.scheduleAt) {
                        commonService.showError("Please enter the schedule at value");
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

        $scope._getSelectedtags = function () {
            let tags = [];
            ctrl.selectedTags.forEach(function(item) {
                tags.push(item.name);
            });
            return tags;
        };

        $scope.testClick = function () {
            //console.log(ctrl.selectedTag);
            $scope._getSelectedtags().forEach(function(item) {
               console.log(item);
            });

        };

        $scope.submitClick = function (formIsValid) {
            if(!formIsValid) {
               commonService.showError("Form is invalid");
               return;
            }
            console.log($scope.selectedSuite);
            $scope.jobId = null;
            let payload = {};
            payload["suite_path"] = $scope.selectedSuite;
            payload["build_url"] = $scope.buildUrl;
            payload["tags"] = $scope._getSelectedtags();
            if($scope.emails) {
                $scope.emails = $scope.emails.split(",");
                payload["email_list"] = $scope.emails
            }

            if($scope.schedulingOptions) {
                payload = $scope.getSchedulingOptions(payload);
            }
            $http.post('/regression/submit_job', payload).then(function(result){
                $scope.jobId = parseInt(result.data);
                $window.location.href = "/regression/suite_detail/" + $scope.jobId;
                commonService.showSuccess("Job " + $scope.jobId + " Submitted");
            }).catch(function(result) {
                commonService.showError("Unable to submit job");
            });
        }

    }

    angular.module('qa-dashboard').component('submitJob', {
        templateUrl: '/static/qa_dashboard/submit_job.html',
        controller: SubmitJob,
        bindings: {
        }
    }).filter('propsFilter', function () {
    return function (items, props) {
        let out = [];

        if (angular.isArray(items)) {
            let keys = Object.keys(props);

            items.forEach(function (item) {
                let itemMatches = false;

                for (let i = 0; i < keys.length; i++) {
                    let prop = keys[i];
                    let text = props[prop].toLowerCase();
                    if (item[prop].toString().toLowerCase().indexOf(text) !== -1) {
                        itemMatches = true;
                        break;
                    }
                }
                if (itemMatches) {
                    out.push(item);
                }
            });
        } else {
            // Let the output be the input untouched
            out = items;
        }

        return out;
    };
});

})(window.angular);
