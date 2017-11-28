(function (angular) {
    'use strict';

    function SendTrafficController($scope, $http, $timeout) {
        let pollInterval = 2000;
        let ctrl = this;
        $scope.tgTypes = {"fio": "FIO", "iperf": "IPerf"};

        ctrl.$onInit = function () {
		$scope.selectedTg = null;
		$scope.fioNrFiles = 1;
		$scope.fioBlockSize = "4k";
		$scope.fioSize = "128k";
		$scope.playing = false;

        };
        $scope.tgSelection = function (selectedTg) {
            $scope.selectedTg = selectedTg;
            console.log(selectedTg);
        };


        $scope.play = function () {
            $scope.logs = "";
            let payload = {};
            payload["block_size"] = $scope.fioBlockSize;
            payload["size"] = $scope.fioSize;
            payload["nr_files"] = $scope.fioNrFiles;
            $http.post('/tools/tg/fio/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function (response) {
                $scope.playing = true;
                getTrafficTaskStatus(ctrl.topologySessionId);
            })
        };
        let getTrafficTaskStatus = function (sessionId) {
            $http.get("/tools/tg/traffic_task_status/" + sessionId.toString()).then(function (result) {
                let status = result.data["status"];
                if ((status === "NOT_RUN") || (status === "IN_PROGRESS")) {
                    $timeout(function () {
                        getTrafficTaskStatus(sessionId)
                    }, pollInterval);
                } else {
                    $scope.playing = false;
                    $scope.logs = result.data.logs.toString();
                    const regex = /Run status group.*',/g;
                    let s = regex.exec($scope.logs);
                    if(s.length) {
                        $scope.logs = s[0].replace(/\\n/g, "\n");
                    }

                    let cleanLogs = [];
                    const read_regex = /READ.*io=(.*B) /;
                    let r_s = regex.exec($scope.logs);
                    if(r_s.length) {
                        cleanLogs.push(s[1]);
                    }
                    const write_regex = /WRITE.*io=(.*B) /;
                    let w_s = regex.exec($scope.logs);
                    if(w_s.length) {
                        cleanLogs.push(s[1]);
                    }
                    $scope.logs = cleanLogs;



                }
            }).catch(function (result) {
                // task error TODO
                $scope.playing = false;
            });
        };


    }

    angular.module('tools').component('sendTraffic', {
        templateUrl: '/static/send_traffic.html',
        controller: SendTrafficController,
        bindings: {
            f1: '=',
            topologySessionId: '='
        }
    });
})(window.angular);
