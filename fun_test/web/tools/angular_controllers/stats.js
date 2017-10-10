(function (angular) {
    'use strict';

    function StatsController($scope, $http, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.charting = false;
            $scope.series = ['F1', 'F2', 'F3'];
            $scope.buttonText = "Start";
            $scope.playIcon = "glyphicon-play";
            $scope.currentValues = {};
            $scope.title = "Reads";

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
            angular.forEach($scope.series, function (seriesName) {
                $scope.currentValues[seriesName] = $scope.getRandomId();
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
