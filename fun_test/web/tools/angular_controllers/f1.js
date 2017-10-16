(function (angular) {
    'use strict';

    function F1Controller($scope, $http, $timeout) {
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
            ctrl.f1.volumeUuids = [];
            ctrl.f1.rdsVolumeUuids = [];
            ctrl.f1.replicaVolumeUuids = [];
            ctrl.f1.attached_ns_id = false;
            $scope.checkVolumes();  //TODO


        };

        $scope.checkVolumes = function () {
            $http.get('/tools/f1/storage_volumes/' + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function (volumeResponse) {
                if (volumeResponse.data.data) {
                    if ('VOL_TYPE_BLK_RDS' in volumeResponse.data.data) {
                        let rdsBlock = volumeResponse.data.data.VOL_TYPE_BLK_RDS;
                        ctrl.f1.volumeRds = rdsBlock;
                        ctrl.f1.rdsVolumeUuids = [];
                        angular.forEach(rdsBlock, function (value, key) {
                            ctrl.f1.rdsVolumeUuids.push(key);
                        });
                    }
                    if ('VOL_TYPE_BLK_LOCAL_THIN' in volumeResponse.data.data) {
                        let localBlock = volumeResponse.data.data.VOL_TYPE_BLK_LOCAL_THIN;
                        ctrl.f1.volumeThin = localBlock;
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
                    if ('VOL_TYPE_BLK_REPLICA' in volumeResponse.data.data) {
                        let replicaBlock = volumeResponse.data.data.VOL_TYPE_BLK_REPLICA;
                        ctrl.f1.volumeReplica = replicaBlock;
                        ctrl.f1.replicaVolumeUuids = [];
                        angular.forEach(replicaBlock, function (value, key) {
                            ctrl.f1.replicaVolumeUuids.push(key);
                        });
                    }
                }
            });
            $timeout($scope.checkVolumes, 10000);
        };


        $scope.workFlowSelection = function (selectedWorkFlow) {
            $scope.selectedWorkFlow = selectedWorkFlow;
            ctrl.setCommonWorkFlow({selectedWorkFlow: selectedWorkFlow, f1: ctrl.f1});
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
            setActiveTab: '&',
            topologySessionId: '<'
        }
    });

})(window.angular);
