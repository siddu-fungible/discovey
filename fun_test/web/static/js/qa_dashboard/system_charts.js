'use strict';

function SystemChartsController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.chart1Name = "Best time for 1 malloc/free (WU)";
        $scope.model1Name = "AllocSpeedPerformance";
        $scope.chart2Name = "Best time for 1 malloc/free (Threaded)";
        $scope.model2Name = "AllocSpeedPerformance";
        $scope.fetchJenkinsJobIdMap();
        $scope.buildInfo = null;
    };

    $scope.fetchJenkinsJobIdMap = () => {
        commonService.apiGet('/regression/jenkins_job_id_maps').then((data) => {
            $scope.jenkinsJobIdMap = data;
            console.log($scope.jenkinsJobIdMap);
            commonService.apiGet('/regression/build_to_date_map').then((data) => {
                $scope.buildInfo = data;
            })
        })
    };

    $scope.pointClickCallback = (point) => {
        console.log(point);
    };

    $scope.xAxisFormatter = (value) => {
        let s = "Error";
        let key = parseInt(value);
        if (key in $scope.buildInfo) {
            s = $scope.buildInfo[key]["software_date"].toString();
            let thisYear = new Date().getFullYear();
            s = s.replace(thisYear, "");
            let r = /(\d\d+)(\d\d)/g;
            let match = r.exec(s);
            s = match[1] + "/" + match[2];
        }
        return s;
    };

    $scope.tooltipFormatter = (x, y) => {
        let softwareDate = "Unknown";
        let sdkBranchRef = x;
        let key = parseInt(x);
        if (key in $scope.buildInfo) {
            softwareDate = $scope.buildInfo[key]["software_date"];
        }
        let s = "<b>SDK branch git ref:</b> " + sdkBranchRef + "<br>";
        s += "<b>Software date:</b> " + softwareDate + "<br>";
        s += "<b>Value:</b> " + y + "<br>";
        return s;
    }
}

angular.module('qa-dashboard').controller("systemChartsController", SystemChartsController);
