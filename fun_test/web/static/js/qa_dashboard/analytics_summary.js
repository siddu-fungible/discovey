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
        let features = ["networking", "storage", "security", "system"];
        let results = ["PASSED", "FAILED"];
        features.forEach((feature) => {
            for (let i = 0; i < 5; i++ ) {
                let oneEntry = {};
                oneEntry.feature = feature;
                oneEntry.metric = "Metric " + Math.floor(Math.random() * 20);
                oneEntry.palladium_actual = Math.floor(Math.random() * 20);
                oneEntry.palladium_goal = Math.floor(Math.random() * 20);
                oneEntry.f1_goal = Math.floor(Math.random() * 20);
                let resultIndex = Math.floor(Math.random() * 3) % 2;
                //console.log(resultIndex);
                oneEntry.result = results[resultIndex];
                $scope.table.push(oneEntry);

            }
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

