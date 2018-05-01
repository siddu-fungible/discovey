'use strict';

function AtomicMetricController($scope, commonService, $timeout) {
    let ctrl = this;

    this.$onInit = function () {
        $scope.modelName = ctrl.modelName;
        $scope.chartName = ctrl.chartName;
        $scope.fetchJenkinsJobIdMap();
        $scope.atomic = true;

    };

    $scope.fetchJenkinsJobIdMap = () => {
        commonService.apiGet('/regression/jenkins_job_id_maps').then((data) => {
            $scope.jenkinsJobIdMap = data;
            //console.log($scope.jenkinsJobIdMap);
            commonService.apiGet('/regression/build_to_date_map').then((data) => {
                $scope.buildInfo = data;
            })
        })
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
        let hardwareVersion = "Unknown";
        let sdkBranchRef = x;
        let key = parseInt(x);
        if (key in $scope.buildInfo) {
            softwareDate = $scope.buildInfo[key]["software_date"];
            hardwareVersion = $scope.buildInfo[key]["hardware_version"];
        }
        let s = "<b>SDK branch git ref:</b> " + sdkBranchRef + "<br>";
        s += "<b>Software date:</b> " + softwareDate + "<br>";
        s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
        s += "<b>Value:</b> " + y + "<br>";
        return s;
    };




}

angular.module('qa-dashboard').component('atomicMetric', {
        templateUrl: '/static/qa_dashboard/atomic_metric.html',
        controller: AtomicMetricController,
        bindings: {
            modelName: '@',
            chartName: '@'
        }
});

angular.module('qa-dashboard').controller("atomicMetricController", AtomicMetricController);
angular.module('qa-dashboard').filter('unsafe', function($sce) { return $sce.trustAsHtml; });





