(function (angular) {
    'use strict';

    function SubmitJob($scope,$http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            console.log(ctrl);
            $scope.selectedSuite = null;
            $scope.selectedInfo = null;
            $http.get("/regression/suites").then(function(result) {
                $scope.suitesInfo = result.data;
            });
        };

        $scope.changedValue = function(selectedSuite) {
            $scope.selectedInfo = $scope.suitesInfo[selectedSuite];
        }



    }

    angular.module('qa-dashboard').component('submitJob', {
        templateUrl: '/static/qa_dashboard/submit_job.html',
        controller: SubmitJob,
        bindings: {
        }
    })

})(window.angular);
