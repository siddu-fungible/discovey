(function (angular) {
    'use strict';

    function CreateVolumeController($scope, $element, $attrs) {
        let ctrl = this;

        ctrl.$onInit = function () {
        };
    }

    angular.module('tools').component('createVolume', {
        templateUrl: '/static/create_volume.html',
        controller: CreateVolumeController,
        bindings: {
            obj: '<'
        }
    });
})(window.angular);
