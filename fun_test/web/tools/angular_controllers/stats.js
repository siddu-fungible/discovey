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
            //$scope.buttonText = "Start";
            $scope.buttonText = "Fetch stats";
            $scope.playIcon = "glyphicon-play";
            $scope.currentReadValues = {};
            $scope.currentWriteValues = {};
            $scope.readsTitle = "Reads";
            $scope.writesTitle = "Writes";
            $scope.width = "100px";
            $scope.height = "100px";

        };

        $scope.checkVolumes = function () {

        };
        
        $scope.startChart = function () {
            //console.log(ctrl);
            $scope.charting = !$scope.charting;
            $scope.pullStats();
            /*if($scope.charting) {
                $scope.buttonText = "Stop";
                $scope.playIcon = "glyphicon-pause";
                $scope.pullStats();
            } else {
                $scope.buttonText = "Start";
                $scope.playIcon = "glyphicon-play";
            }*/
        };

        $scope.startIkvChart = function () {
            $scope.pullIkvStats(); 
        }

        $scope.pullIkvStats = function () {
            console.log("Pulling");
            $scope.newReadStats = {};
            $scope.newWriteStats = {};
            angular.forEach($scope.series, function (seriesName) {
                $http.get("/tools/f1/ikv_stats/" + ctrl.topologySessionId + "/" + seriesName).then(function (result) {
                    if (result.data.status === "PASSED") {
                        let d = result.data.data;
                        if(d) {
                            $scope.ikvInfo = d[0];
                        }
                    }
                });
            });
          
            if($scope.charting) {
                $timeout($scope.pullStats, 5000);
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
                                $scope.currentReadValues[seriesName] = numReads;
                                $scope.currentWriteValues[seriesName] = numWrites;
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
                                        $scope.currentReadValues[seriesName] = numReads;
                                        $scope.currentWriteValues[seriesName] = numWrites;
                                    }
                                });

                            }
                        }
                    }
                    /*
                    if(Object.keys($scope.newReadStats).length === $scope.series.length) {
                        if(Object.keys($scope.newReadStats).length > 0) {
                            $scope.currentReadValues = JSON.parse(JSON.stringify($scope.newReadStats));
                        }
                    };
                    if(Object.keys($scope.newWriteStats).length === $scope.series.length) {
                        if(Object.keys($scope.newWriteStats).length > 0) {
                            $scope.currentWriteValues = JSON.parse(JSON.stringify($scope.newWriteStats));
                        }
                    };*/
                });
            });
          
            if($scope.charting) {
                $timeout($scope.pullStats, 5000);
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
            f1s: '=',
            workFlows: '<',
            replaceIpDot: '&',
            setCommonWorkFlow: '&',
            setActiveTab: '&',
            topologySessionId: '<',
            commonTrafficWorkFlow: '<'
        }
    });

})(window.angular);
