(function (angular) {
    'use strict';

    function F1DetailController($scope, $http, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {
            console.log(ctrl);
            $scope.f1 = ctrl.f1;
            $scope.vpWus = null;
            $scope.syncing = false;
            $scope.syncTimer = null;
            $scope.charting = null;
        };

        $scope.sync = function () {
            if($scope.syncing) {
                let payload = {};
                payload["ip"] = $scope.f1.ip;
                payload["port"] = 5001;
                $http.post("/tools/f1/detail", payload).then(function (result) {
                    if (result.data.status === "PASSED") {
                        $scope.vpWus = result.data.data["per_vp"];
                    }
                });
                $scope.syncTimer = $timeout($scope.sync, 5000);
            }
        };

        $scope.toggleChart = function (event) {
            //console.log($scope.charting);
            if (event.target.checked) {
                $scope.charting = true;
            } else {
                $scope.charting = false;
            }
        };

        $scope.toggleSync = function (event) {
            if (event.target.checked) {
                $scope.syncing = true;
                $scope.sync();
            } else {
                $scope.syncing = false;
                console.log($scope.syncing);
                $timeout.cancel($scope.syncTimer);

            }
        };
    }

    angular.module('tools').component('f1Detail', {
        templateUrl: '/static/f1_detail.html',
        controller: F1DetailController,
        bindings: {
            f1: '='
        }
    });

})(window.angular);
