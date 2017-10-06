(function (angular) {
    'use strict';

    function AttachVolumeController($scope, $element) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.uuid = null;
            $scope.nsid = null;
        };

    }

    angular.module('tools').component('attachVolume', {
        templateUrl: '/static/attach_volume.html',
        controller: AttachVolumeController
    });
})(window.angular);
