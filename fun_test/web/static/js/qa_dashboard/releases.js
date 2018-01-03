(function (angular) {
    'use strict';

    function ReleasesController($scope, $http, $window, $timeout, commonService) {
        let ctrl = this;

        ctrl.$onInit = function () {
            $scope.fetchReleases();
        };

        $scope.fetchReleases = function () {
            commonService.apiGet('/tcm/releases', "fetchReleases").then(function (data) {
                let instances = data;
                instances.forEach(function(instance) {
                    let suite_execution_id = instance.fields.suite_execution_id;

                });
            })
        };

    }

    angular.module('qa-dashboard').controller("releasesController", ReleasesController);

})(window.angular);
