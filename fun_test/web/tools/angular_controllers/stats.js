(function (angular) {
    'use strict';

    function StatsController($scope, $http, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.charting = false;
            $scope.series = ['1-1', '1-2', '1-3', '1-4'];
            //$scope.buttonText = "Start";
            //$scope.buttonText = "Toggle stats";
            $scope.playIcon = "glyphicon-play";
            $scope.currentReadValues = {};
            $scope.currentWriteValues = {};

            for(let i = 0; i < $scope.series.length; i++) {
                $scope.currentReadValues[$scope.series[i]] = 0;
                $scope.currentWriteValues[$scope.series[i]] = 0;
            }

            $scope.readsTitle = "Reads";
            $scope.writesTitle = "Writes";
            $scope.width = "100px";
            $scope.height = "100px";
            $scope.ikvInfo = null;

            //$scope.startChart();


  $scope.options = {
            chart: {
                type: 'pieChart',
                height: 500,
                width: 500,
                x: function(d){return d.key;},
                y: function(d){return d.y;},
                showLabels: true,
                duration: 500,
                labelThreshold: 0.01,
                labelSunbeamLayout: true,
                legend: {
                    margin: {
                        top: 5,
                        right: 35,
                        bottom: 5,
                        left: 0
                    }
                }
            }
        };
        $scope.data = [];
        };
        

        $scope.checkVolumes = function () {

        };
        
        $scope.startChart = function () {
            //console.log(ctrl);
            $scope.charting = !$scope.charting;
            $scope.pullStats();
            /*
            if($scope.charting) {
                $scope.buttonText = "Stop";
                $scope.playIcon = "glyphicon-pause";
                $scope.pullStats();
            } else {
                $scope.buttonText = "Start";
                $scope.playIcon = "glyphicon-play";
            }*/
        };

        $scope.startIkvChart = function () {
            $scope.ikvInfo = null;
            $scope.pullIkvStats(); 
        }

        $scope.pullIkvStats = function () {




            console.log("Pulling");
            $scope.newReadStats = {};
            $scope.newWriteStats = {};
            angular.forEach($scope.series, function (seriesName) {
                $http.get("/tools/f1/ikv_stats/" + ctrl.topologySessionId + "/" + ctrl.currentWorkFlowF1.name).then(function (result) {
                    if (result.data.status === "PASSED") {
                        let d = result.data.data;
                        if(d) {
                            $scope.ikvInfo = d[0];
                            let availableSpace = $scope.ikvInfo["LIKV space"];
                            let usedSpace = $scope.ikvInfo["LIKV used space"];
                            let freeSpace = availableSpace - usedSpace;
		            $scope.data = [{key: "Used Space", y: usedSpace}, {key: "Free Space", y: freeSpace}];
                        }
                    }
                });
            });
          
            if($scope.charting) {
                $timeout($scope.pullStats, 4000);
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
                            } else if('VOL_TYPE_BLK_REPLICA' in d) {
                                let numReads = 0;
                                let numWrites = 0;
                                angular.forEach(d.VOL_TYPE_BLK_REPLICA, function(value, key) {
                                    numReads += value.num_reads;
                                    numWrites += value.num_writes;
                                });
                                $scope.currentReadValues[seriesName] = numReads;
                                $scope.currentWriteValues[seriesName] = numWrites;
                               
                            }
                            /*
                            else {
            
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

                            }*/
                        }
                    }
                });
            });
          
            if($scope.charting) {
                $timeout($scope.pullStats, 2000);
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
            commonTrafficWorkFlow: '<',
            currentWorkFlowF1: '<'
        }
    });

})(window.angular);
