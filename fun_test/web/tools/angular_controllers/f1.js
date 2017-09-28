(function (angular) {
    'use strict';

    function F1Controller($scope, $http) {
        let ctrl = this;

        ctrl.$onInit = function () {
            //console.log(ctrl.replaceIpDot);
            $scope.selectedWorkFlow = null;
            $scope.progressLabel = true;
            $scope.progressIcon = false;
            $scope.progressDiv = false;
            $scope.progressBarWidth = 0;
            $scope.hasVolumes = false;
            $scope.hasReplicatedVolumes = false;

        };

        $scope.workFlowSelection = function (selectedWorkFlow) {
            $scope.selectedWorkFlow = selectedWorkFlow;
            ctrl.setCommonWorkFlow({selectedWorkFlow: selectedWorkFlow});
            //ctrl.setcwf("John");

            console.log(selectedWorkFlow);

        };

        $scope.detailsViewClick = function () {
            ctrl.setActiveTab({tabName: "details", f1: ctrl.f1});
        };

        $scope.startWorkFlow = function () {
            $scope.progressLabel = false;

            let payload = {"f1": ctrl.f1.ip, workFlow: $scope.commonWorkFlow};
            let replacedIp = ctrl.replaceIpDot({iP: ctrl.f1.ip});
            $scope.progressDiv = true;
            $scope.progressBarWidth = 50;

            $http.post("/tools/f1/start_workflow_step", payload).then(function (result) {
                $scope.progressBarWidth = 100;
                $scope.progressDiv = false;
                $scope.progressIcon = true;
                $scope.hasVolumes = true;
                $scope.hasReplicatedVolumes = true;

            })
         };
    }

    angular.module('tools').component('f1', {
        templateUrl: '/static/f1.html',
        controller: F1Controller,
        bindings: {
            f1: '=',
            workFlows: '<',
            replaceIpDot: '&',
            setCommonWorkFlow: '&',
            setActiveTab: '&'
        }
    });

})(window.angular);
