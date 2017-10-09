(function (angular) {
    'use strict';

    function CreateRdsVolumeController($scope, $http, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.status = "idle";
            $scope.name = "volume";
            $scope.capacity = 1073741824;
            $scope.blockSize = 4096;
            $scope.errorMessage = null;
            $scope.rdsVolumeUuids = [];
            $scope.selectedRemoteIp = null;
            $scope.remoteNsId = 1;
        };

        $scope.clickApply = function () {
            $scope.errorMessage = null;
            let payload = {};
            payload["name"] = $scope.name;
            payload["capacity"] = $scope.capacity;
            payload["block_size"] = $scope.blockSize;
            payload["remote_nsid"] = $scope.remoteNsId;
            payload["remote_ip"] = $scope.selectedRemoteIp;
            $scope.status = "processing";
            $http.post('/tools/f1/create_rds_volume/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){
                $scope.status = "pass";
                if (!response.data["status"]) {
                    $scope.errorMessage = response.data["error_message"];
                    $scope.status = "fail";
                } else {
                    $timeout(function () {
			    ctrl.f1.rdsVolumeUuids = [];
			    $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function(volumeResponse) {
				let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_RDS;
				$scope.rdsVolumeUuids = [];
				ctrl.f1.rdsVolumeUuids = [];
				angular.forEach(localBlock, function (value, key) {
				    $scope.rdsVolumeUuids.push(key);
				    ctrl.f1.rdsVolumeUuids.push(key);
				});
			    });
                    }, 5000);
                }
            })
            .catch(function(data) {
                $scope.status = "fail";
                $scope.errorMessage = data;
            });
        };

    }

    angular.module('tools').component('createRdsVolume', {
        templateUrl: '/static/create_rds_volume.html',
        controller: CreateRdsVolumeController,
        bindings: {
            obj: '<',
            f1: '=',
            f1s: '=',
            topologySessionId: '='
        }
    });
})(window.angular);
