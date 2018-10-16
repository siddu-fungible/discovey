'use strict';

function ScoreTableController($scope, commonService, $timeout) {
    let ctrl = this;

    this.$onInit = function () {
        $scope.modelName = ctrl.modelName;
        $scope.chartName = ctrl.chartName;
        $scope.metricId = -1;
        $scope.rows = {};
        let payload = {};
        payload["chart_name"] = $scope.chartName;
        payload["metric_model_name"] = $scope.modelName;
        let self = $scope;
        if($scope.chartName) {
            commonService.apiPost("/metrics/chart_info", payload, "Scores Table: chart_info").then((chartInfo) => {
                if(chartInfo) {
                  self.metricId = chartInfo["metric_id"];
                payload = {};
                payload["metric_id"] = $scope.metricId;
                self.chartName = $scope.chartName;
                self.modelName = $scope.modelName;
                let rows = {};
                commonService.apiPost("/metrics/scores", payload, "Scores Table: scores").then((response) => {
                    if (response.length !== 0) {
                        let keyList = Object.keys(response.scores);
                        keyList.sort();
                        keyList.forEach((dateTime) => {
                            let d = new Date(dateTime * 1000).toISOString();
                            rows[d] = response.scores[dateTime].score;
                        });
                    }
                    self.rows = rows;
                });
                }

            });
        }

    };
}

angular.module('qa-dashboard').component("scoreTable", {
        templateUrl: '/static/qa_dashboard/scores_table.html',
        bindings: {
                   modelName: '@',
                    chartName: '@'
                  },
        controller: ScoreTableController
 });