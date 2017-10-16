(function (angular) {
    'use strict';

    function F1DetailController($scope, $http, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {
            console.log(ctrl);
            //$scope.f1 = ctrl.f1;
            $scope.vpWus = null;
            $scope.syncing = false;
            $scope.syncTimer = null;
            $scope.charting = null;
            $scope.series = ['Sent', 'Received'];
            //$scope.width = "100px";
            //$scope.height = "100px";
        };

        $scope.$watch('ctrl.f1', function () {
            $scope.f1 = ctrl.f1;
        });

        $scope.sync = function () {
            if($scope.syncing) {
                let payload = {};
                payload["ip"] = ctrl.f1.ip;
                payload["port"] = parseInt(ctrl.f1.dpcsh_port);
                $http.post("/tools/f1/detail", payload).then(function (result) {
                    if (result.data.status === "PASSED") {
                        $scope.vpWus = result.data.data["per_vp"];
                        /*$scope.vpWusArray = Object.keys($scope.vpWus).map(function(key) {
                            return $scope.vpWus[key];
                        });*/
                        let i = 0;
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
    })
    .filter('toArray', function () {
        return function (obj, addKey) {
            if (!angular.isObject(obj)) return obj;
            if ( addKey === false ) {
                return Object.keys(obj).map(function(key) {
                    return obj[key];
               });
            } else {
               return Object.keys(obj).map(function (key) {
                   var value = obj[key];
                   //return angular.isObject(value) ? Object.defineProperty(value, '$key', { enumerable: false, value: key}) : { $key: key, $value: value };
                   return { $key: key, $value: value };
               });
            }
        };
    });

})(window.angular);
