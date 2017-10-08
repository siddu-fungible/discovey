(function (angular) {
    'use strict';

    function AttachTgController($scope, $http, $timeout) {
        let pollInterval = 2000;
        let ctrl = this;
        $scope.tgTypes = {"fio": "FIO", "iperf": "IPerf"};
        $scope.selectedTg = null;
        $scope.fioNrFiles = 1;
        $scope.fioBlockSize = "4k";
        $scope.fioSize = "128k";

        ctrl.$onInit = function () {
            $scope.playing = false;
        };
        $scope.tgSelection = function (selectedTg) {
            $scope.selectedTg = selectedTg;
            console.log(selectedTg);
        };

        $scope.play = function () {
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
                }
            }).catch(function (result) {
                // task error TODO
                $scope.playing = false;
            });
        };


    }

    angular.module('tools').component('attachTg', {
        templateUrl: '/static/attach_tg.html',
        controller: AttachTgController,
        bindings: {
            f1: '=',
            topologySessionId: '='
        }
    });
})(window.angular);
