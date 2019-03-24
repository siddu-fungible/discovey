'use strict';

function AnalyticsSummaryController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.table = [];
        $scope.populateTable();

        $scope.chart1Name = "BLT Performance IOPS";
        $scope.model1Name = "PerformanceBlt";
        $scope.chart2Name = "BLT Write IOPS";
        $scope.model2Name = "VolumePerformance";
        $scope.chart3Name = "BLT Write Latency";
        $scope.model3Name = "VolumePerformance";

        $scope.chartInfo = {};
        $scope.chartInfo["BLT Performance IOPS"] = {"model": "PerformanceBlt"};
        $scope.chartInfo["BLT Write IOPS"] = {"model": "VolumePerformance"};
        $scope.chartInfo["BLT Write Latency"] = {"model": "VolumePerformance"};


        $scope.chartNames = [$scope.chart1Name, $scope.chart2Name, $scope.chart3Name];
        $scope.currentChart = null;

    };

    $scope.populateTable = () => {
        let features = ["networking", "storage", "accelerators"];

        let featureMetricMapping = {};
        featureMetricMapping["networking"] = ["Packets per second", "Instructions per packet"];
        featureMetricMapping["storage"] = ["Raw Volume MIOPS", "Durable Volume MIOPS", "Raw Volume Latency local", "Raw Volume Latency Remote"];
        featureMetricMapping["accelerators"] = ["Crypto AES-GCM/XTS Throughput", "Hash Engines", "Regex Throughput", "EC Throughput", "ZIP throughput"];


        let results = ["PASSED", "FAILED"];
        features.forEach((feature) => {
            featureMetricMapping[feature].forEach((metric) => {
                let oneEntry = {};
                oneEntry.feature = feature;
                oneEntry.metric = metric;
                oneEntry.palladium_actual = Math.floor(Math.random() * 20);
                oneEntry.palladium_goal = Math.floor(Math.random() * 20);
                oneEntry.f1_goal = Math.floor(Math.random() * 20);
                let resultIndex = Math.floor(Math.random() * 3) % 2;
                //console.log(resultIndex);
                oneEntry.result = results[resultIndex];
                $scope.table.push(oneEntry);
            });


        })
    };

    $scope.getStatusIcon = (result) => {
        let s = "<i class='fa fa-check-circle text-success'></i>";
        if(result === "FAILED") {
            s = "<i class='fa fa-thumbs-down text-danger'></i>";
        }
        return s;
    };

    $scope.showChart = () => {
        let index =  Math.floor(Math.random() * 3) % 3;
        console.log(index);
        $scope.chartName = $scope.chartNames[index];
    }
}



angular.module('qa-dashboard').controller("analyticsSummaryController", AnalyticsSummaryController);
angular.module('qa-dashboard').component('analyticsSummary', {
        templateUrl: '/static/qa_dashboard/analytics_summary_template.html',
        controller: AnalyticsSummaryController
});

