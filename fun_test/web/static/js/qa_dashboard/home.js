'use strict';

function HomeController($scope, commonService, $timeout) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";

    };

}

angular.module('qa-dashboard').controller("homeController", HomeController);

