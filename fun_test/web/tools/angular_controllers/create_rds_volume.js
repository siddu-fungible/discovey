(function (angular) {
    'use strict';

    function CreateRdsVolumeController($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.name = "volume";
            $scope.capacity = 536870912;
            $scope.blockSize = 4096;
            $scope.remoteIp = "127.0.0.1";
            $scope.remoteNsId = null;
        };

        $scope.clickApply = function () {
            let payload = {};
            payload["name"] = $scope.name;
            payload["capacity"] = $scope.capacity;
            payload["block_size"] = $scope.blockSize;
            payload["remote_ip"] = $scope.remoteIp;
            payload["remote_nsid"] = $scope.remoteNsId;
            $http.post('/tools/f1/create_rds_volume/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){

            })
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
