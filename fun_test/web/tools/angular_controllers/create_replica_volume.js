(function (angular) {
    'use strict';

    function CreateReplicaVolumeController($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.status = "idle";
            $scope.logs = [];
            $scope.name = "volume";
            $scope.capacity = 1073741824;
            $scope.blockSize = 4096;
            $scope.errorMessage = null;
            $scope.replicaVolumeUuids = [];
            $scope.selectedUuids = null;
            ctrl.f1.rdsVolumeUuids = [];
            ctrl.f1.rdsVolumeUuids = [];
            $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function (volumeResponse) {
                let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_RDS;
                $scope.rdsVolumeUuids = [];
                ctrl.f1.rdsVolumeUuids = [];
                angular.forEach(localBlock, function (value, key) {
                    $scope.rdsVolumeUuids.push(key);
                    ctrl.f1.rdsVolumeUuids.push(key);
                });
            });

        };

        $scope.clickApply = function () {
            $scope.errorMessage = null;
            let payload = {};
            payload["name"] = $scope.name;
            payload["capacity"] = $scope.capacity;
            payload["block_size"] = $scope.blockSize;
            payload["pvol_id"] = $scope.selectedUuids;
            console.log($scope.selectedUuids);
            $scope.status = "processing";
            $http.post('/tools/f1/create_replica_volume/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function (response) {
                $scope.status = "pass";
                $scope.logs = [];
                let responseLogs = response.data.logs;
                for (let i = 0; i < responseLogs.length; i++) {
                    $scope.logs.push(responseLogs[i] + "\n");
                    $scope.logs.push("-----------------------------------\n");
                }
                if (!response.data["status"]) {
                    $scope.errorMessage = response.data["error_message"];
                    $scope.status = "fail";
                } else {
                    $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function (volumeResponse) {
                        let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_REPLICA;
                        angular.forEach(localBlock, function (value, key) {
                            $scope.replicaVolumeUuids.push(key);
                            ctrl.f1.replicaVolumeUuids.push(key);
                        });
                    });
                }
            })
                .catch(function (data) {
                    $scope.status = "fail";
                    $scope.errorMessage = data;
                });
        };

    }

    angular.module('tools').component('createReplicaVolume', {
        templateUrl: '/static/create_replica_volume.html',
        controller: CreateReplicaVolumeController,
        bindings: {
            obj: '<',
            f1: '=',
            topologySessionId: '='
        }
    });
})(window.angular);
