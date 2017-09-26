(function (angular) {
    'use strict';

    function AttachTgController($scope) {
        let ctrl = this;
        $scope.tgTypes = {"fio": "FIO", "iperf": "IPerf"};
        $scope.selectedTg = null;

        ctrl.$onInit = function () {

        };
        $scope.tgSelection = function (selectedTg) {
            $scope.selectedTg = selectedTg;
            console.log(selectedTg);
        };
    }

    angular.module('tools').component('attachTg', {
        templateUrl: '/static/attach_tg.html',
        controller: AttachTgController
    });
})(window.angular);
