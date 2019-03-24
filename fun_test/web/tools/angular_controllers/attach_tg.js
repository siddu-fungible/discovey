(function (angular) {
    'use strict';

    function AttachTgController($scope, $http, $timeout) {
        let pollInterval = 2000;
        let ctrl = this;

        ctrl.$onInit = function () {

            $scope.status = "idle";
            $scope.logs = [];

            ctrl.f1.replicaVolumeUuids = [];
            $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function(volumeResponse) {
                let replicaBlock = volumeResponse.data.data.VOL_TYPE_BLK_REPLICA;
                angular.forEach(replicaBlock, function (value, key) {
                    ctrl.f1.replicaVolumeUuids.push(key);
                });
            });

            ctrl.f1.volumeUuids = [];
            $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function(volumeResponse) {
                let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_LOCAL_THIN;
                angular.forEach(localBlock, function (value, key) {
                    ctrl.f1.volumeUuids.push(key);
                });
            });

        };


        $scope.attach = function () {
            $scope.errorMessage = null;

            $scope.logs = [];
            let payload = {};
            payload["uuid"] = $scope.selectedUuid;
            $scope.status = "processing";


            $http.post('/tools/f1/attach_tg/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){
                ctrl.f1.tgs.push({"ip": response.data});
                $scope.status = "pass";
                $scope.logs = [];
                let responseLogs = ["Attached Tg:" + response.data];
                for (let i = 0; i < responseLogs.length; i++) {
                    $scope.logs.push(responseLogs[i] + "\n");
                    $scope.logs.push("-----------------------------------\n");
                }
                /*
                if (!response.data["status"]) {
                    $scope.errorMessage = response.data["error_message"];
                    $scope.status = "fail";
                } else {
                    $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function(volumeResponse) {
                        let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_LOCAL_THIN;
                        angular.forEach(localBlock, function (value, key) {
                            //$scope.volumeUuids.push(key);
                            ctrl.f1.volumeUuids.push(key);
                        });
                    });
                }*/
            })
            .catch(function(data) {
                $scope.status = "fail";
                $scope.errorMessage = data;
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
