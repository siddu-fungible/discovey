(function (angular) {
    'use strict';

    function StatsController($scope, $http, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.charting = false;
            //$scope.series = ['2-1', '2-2', '2-3', '2-4'];
            //$scope.series = ['2-2', '2-3'];
            //$scope.series = ['2-2', '2-3', '2-1'];
            $scope.series = ['1-1', '1-2', '1-3', '1-4'];
            $scope.buttonText = "Start";
            $scope.playIcon = "glyphicon-play";
            //$scope.currentReadValues = {};
            //$scope.currentWriteValues = {};
            $scope.readsTitle = "Reads";
            $scope.writesTitle = "Writes";
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
            $scope.newReadStats = {};
            $scope.newWriteStats = {};
            angular.forEach($scope.series, function (seriesName) {
                $http.get("/tools/f1/storage_stats/" + ctrl.topologySessionId + "/" + seriesName).then(function (result) {
                    if (result.data.status === "PASSED") {
                        let d = result.data.data;
                        if(d) {
                            if('VOL_TYPE_BLK_LOCAL_THIN' in d) {
                                let numReads = 0;
                                let numWrites = 0;
                                angular.forEach(d.VOL_TYPE_BLK_LOCAL_THIN, function(value, key) {
                                    numReads += value.num_reads;
                                    numWrites += value.num_writes;
                                });
                                $scope.newReadStats[seriesName] = numReads;
                                $scope.newWriteStats[seriesName] = numWrites;
                            } else {
            
                                $http.get("/tools/f1/storage_repvol_stats/" + ctrl.topologySessionId + "/" + seriesName).then(function (result) {
                                    let d = result.data.data;
                                    let numReads = 0;
                                    let numWrites = 0;
                                    if("plexes" in d) {
                                        angular.forEach(d.plexes, function (plex) {
                                            if("total_reads" in plex) {
                                                numReads += plex.total_reads;
                                            }
                                            if("total_writes" in plex) {
                                                numWrites += plex.total_writes;
                                            }
                                        });
                                        $scope.newReadStats[seriesName] = numReads;
                                        $scope.newWriteStats[seriesName] = numWrites;
                                    }
                                });

                            }
                        }
                    }
                    if(Object.keys($scope.newReadStats).length === $scope.series.length) {
                        $scope.currentReadValues = $scope.newReadStats;
                    };
                    if(Object.keys($scope.newWriteStats).length === $scope.series.length) {
                        $scope.currentWriteValues = $scope.newWriteStats;
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
