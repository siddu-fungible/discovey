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

        let r = /(\d{4})-(\d{2})-(\d{2})/g;
        let match = r.exec(value);
        if (match) {
            s = match[2] + "/" + match[3];
        } else {
            let i = 0;
        }

        return s;
    };

    $scope.tooltipFormatter = (x, y) => {
        let softwareDate = "Unknown";
        let hardwareVersion = "Unknown";
        let sdkBranch = "Unknown";
        let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
        let match = r.exec(x);
        let key = "";
        if (match) {
            key = match[1];
        }
        if (key in $scope.buildInfo) {
            softwareDate = $scope.buildInfo[key]["software_date"];
            hardwareVersion = $scope.buildInfo[key]["hardware_version"];
            sdkBranch = $scope.buildInfo[key]["fun_sdk_branch"]
        }
        let s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
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





