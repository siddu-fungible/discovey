'use strict';

function AnalyticsSummaryController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.table = [];
        $scope.populateTable();

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
                console.log(resultIndex);
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
    }
}

angular.module('qa-dashboard').controller("analyticsSummaryController", AnalyticsSummaryController);
angular.module('qa-dashboard').component('analyticsSummary', {
        templateUrl: '/static/qa_dashboard/analytics_summary_template.html',
        controller: AnalyticsSummaryController
});

