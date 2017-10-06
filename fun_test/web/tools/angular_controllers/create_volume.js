(function (angular) {
    'use strict';

    function CreateVolumeController($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.status = "idle";
            $scope.name = "volume";
            $scope.capacity = 1073741824;
            $scope.blockSize = 4096;
            $scope.errorMessage = null;
           
        };

        $scope.clickApply = function () {
            $scope.errorMessage = null;
            let payload = {};
            payload["name"] = $scope.name;
            payload["capacity"] = $scope.capacity;
            payload["block_size"] = $scope.blockSize;
            $scope.status = "processing";
            $http.post('/tools/f1/create_blt_volume/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){
                $scope.status = "pass";
                if (!response.data["status"]) {
                    $scope.errorMessage = response.data["error_message"];
                    $scope.status = "fail";
                }
            })
        };

    }

    angular.module('tools').component('createVolume', {
        templateUrl: '/static/create_volume.html',
        controller: CreateVolumeController,
        bindings: {
            obj: '<',
            f1: '=',
            topologySessionId: '='
        }
    });
})(window.angular);
