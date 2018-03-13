'use strict';

function SystemChartsController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.chart1Name = "Best time for 1 malloc/free (WU)";
        $scope.model1Name = "AllocSpeedPerformance";
        $scope.chart2Name = "Best time for 1 malloc/free (Threaded)";
        $scope.model2Name = "AllocSpeedPerformance";
        $scope.fetchJenkinsJobIdMap();
    };

    $scope.fetchJenkinsJobIdMap = () => {
        commonService.apiGet('/regression/jenkins_job_id_maps').then((data) => {
            $scope.jenkinsJobIdMap = data;
            console.log($scope.jenkinsJobIdMap);
        })
    }

}

angular.module('qa-dashboard').controller("systemChartsController", SystemChartsController);
