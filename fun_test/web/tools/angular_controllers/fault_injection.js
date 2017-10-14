(function (angular) {
    'use strict';

    function FaultInjectionController($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.status = "idle";
            $scope.logs = [];
            $scope.errorMessage = null;
            $scope.selectedUuids = null;
            $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function (volumeResponse) {
                if (volumeResponse.data.data) {
                    if ('VOL_TYPE_BLK_LOCAL_THIN' in volumeResponse.data.data) {
                        let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_LOCAL_THIN;
                        ctrl.f1.volumeUuids = [];
                        angular.forEach(localBlock, function (value, key) {
                            ctrl.f1.volumeUuids.push(key);
                            if("attach_nsid" in value) {
                                if(value.attach_nsid === 1) {
                                    ctrl.f1.attached_ns_id = true;
                                }
                            }
                        });
                    }
                }
            });
           
        };

        $scope.clickInjectFault = function () {
            $scope.errorMessage = null;
            let payload = {};
            payload["uuid"] = $scope.selectedUuids;
            console.log($scope.selectedUuids);
            $scope.status = "processing";
            $http.post('/tools/f1/fault_injection/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){
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
                }
            })
            .catch(function(data) {
                $scope.status = "fail";
                $scope.errorMessage = data;
            });
        };

    }

    angular.module('tools').component('faultInjection', {
        templateUrl: '/static/fault_injection.html',
        controller: FaultInjectionController,
        bindings: {
            obj: '<',
            f1: '=',
            topologySessionId: '='
        }
    });
})(window.angular);
