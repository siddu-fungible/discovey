(function (angular) {
    'use strict';

    function StatsController($scope, $http, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.charting = false;
            $scope.series = ['2-1', '2-2', '2-3', '2-4'];
            $scope.buttonText = "Start";
            $scope.playIcon = "glyphicon-play";
            $scope.currentValues = {};
            $scope.title = "Reads";
            $scope.width = "100px";
            $scope.height = "100px";

        };

        $scope.checkVolumes = function () {

        };
        
        $scope.startChart = function () {
            $scope.charting = !$scope.charting;
            if($scope.charting) {
                $scope.buttonText = "Stop";
                $scope.playIcon = "glyphicon-pause";
                $scope.pullStats();
            } else {
                $scope.buttonText = "Start";
                $scope.playIcon = "glyphicon-play";
            }
        };

        $scope.pullStats = function () {
            console.log("Pulling");
            let newStats = {};
            angular.forEach($scope.series, function (seriesName) {
                $scope.currentValues[seriesName] = $scope.getRandomId();
                $http.get("/tools/f1/storage_stats/" + ctrl.topologySessionId + "/" + seriesName).then(function (result) {
                    if (result.data.status === "PASSED") {
                        
                    }
                    if(newStats.length == $scope.series.length) {
                        $scope.currentValues = newStats;
                    };
                });
            });
          
            if($scope.charting) {
                $timeout($scope.pullStats, 3000);
            }

        };

        $scope.getRandomId = function () {
            let min = Math.ceil(0);
            let max = Math.floor(10000);
            return Math.floor(Math.random() * (max - min + 1)) + min;
        };


    }

    angular.module('tools').component('stats', {
        templateUrl: '/static/stats.html',
        controller: StatsController,
        bindings: {
            f1: '=',
            workFlows: '<',
            replaceIpDot: '&',
            setCommonWorkFlow: '&',
            setActiveTab: '&',
            topologySessionId: '<'
        }
    });

})(window.angular);
