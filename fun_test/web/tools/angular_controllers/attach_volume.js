(function (angular) {
    'use strict';

    function AttachVolumeController($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.nsid = 1;
            $scope.errorMessage = null;
            $scope.status = "idle";
            $scope.selectedUuid = null;
            $scope.selectedRemoteIp = null;
        };
        $scope.clickApply = function () {
            $scope.errorMessage = null;
            let payload = {};
            payload["uuid"] = $scope.selectedUuid;
            payload["nsid"] = $scope.nsid;
            payload["remote_ip"] = $scope.selectedRemoteIp;
            $scope.status = "processing";
            $http.post('/tools/f1/attach_volume/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){
                $scope.status = "pass";
                if (!response.data["status"]) {
                    $scope.errorMessage = response.data["error_message"];
                    $scope.status = "fail";
                } else {
                    $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function(volumeResponse) {
                        let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_LOCAL_THIN;
                        ctrl.f1.volumeUuids = [];
                        angular.forEach(localBlock, function (value, key) {
                            ctrl.f1.volumeUuids.push(key);
                        });
                    });
                }
            })
            .catch(function(data) {
                $scope.status = "fail";
                $scope.errorMessage = data;
            });
        };

    }

    angular.module('tools').component('attachVolume', {
        templateUrl: '/static/attach_volume.html',
        controller: AttachVolumeController,
        bindings: {
            f1: '=',
            topologySessionId: '=',
            f1s: '='
        }
    });
})(window.angular);
