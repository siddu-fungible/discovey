(function (angular) {
    'use strict';

    function CreateVolumeController($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.name = "volume";
            $scope.capacity = 536870912;
            $scope.blockSize = 4096;
        };

        $scope.clickApply = function () {
            let payload = {};
            payload["name"] = $scope.name;
            payload["capacity"] = $scope.capacity;
            payload["block_size"] = $scope.blockSize;
            $http.post('/tools/f1/create_blt_volume/' + ctrl.topologySessionId + "/" + ctrl.f1.name, payload).then(function(response){

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
