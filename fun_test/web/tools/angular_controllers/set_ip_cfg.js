(function (angular) {
    'use strict';

    function SetIpCfgController($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.status = "idle";
            $scope.errorMessage = null;
            $scope.selectedRemoteIp = null;
        };

        $scope.clickApply = function () {
            $scope.errorMessage = null;
            let payload = {};
            payload["remote_ip"] = $scope.selectedRemoteIp;
            $scope.status = "processing";
            $http.post('/tools/f1/set_ip_cfg/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){
                $scope.status = "pass";
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

    angular.module('tools').component('setIpCfg', {
        templateUrl: '/static/set_ip_cfg.html',
        controller: SetIpCfgController,
        bindings: {
            obj: '<',
            f1: '=',
            f1s: '=',
            topologySessionId: '='
        }
    });
})(window.angular);
