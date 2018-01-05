'use strict';

/*
let funSpinnerStatusInfo = {
        template: ' <div ng-hide="$ctrl.hideOnIdle && ($ctrl.status === idle)" ng-switch="$ctrl.status">\n' +
    '                    Status:\n' +
    '                    <span ng-switch-default><i class="fa fa-refresh fa-spin fa-2x fa-fw"\n' +
    '                                                           style="color: green"></i>{{ $ctrl.status}}</span>\n' +
    '                    <span ng-switch-when="idle" class="label label-info">IDLE</span>\n' +
    '                    <span ng-switch-when="pass" class="glyphicon glyphicon-ok" style="color:green"></span>\n' +
    '                    <span ng-switch-when="fail" class="glyphicon glyphicon-remove" style="color:red"></span>\n' +
    '                </div>',

        bindings: {
                    status: '<',
                    hideOnIdle: '<'
                  },
        controller: FunSpinnerStatusController
 };


function FunSpinnerStatusController($scope) {
    $scope.idle = "idle";
}

let funSpinnerStatusComponent = {"name": "funSpinnerStatus", "info": funSpinnerStatusInfo};
*/

function FunSpinnerStatusController($scope) {
    $scope.idle = "idle";
}

angular.module('qa-dashboard').component("funSpinnerStatus", {
        template: ' <div ng-hide="$ctrl.hideOnIdle && ($ctrl.status === idle)" ng-switch="$ctrl.status">\n' +
    '                    Status:\n' +
    '                    <span ng-switch-default><i class="fa fa-refresh fa-spin fa-2x fa-fw"\n' +
    '                                                           style="color: green"></i>{{ $ctrl.status}}</span>\n' +
    '                    <span ng-switch-when="idle" class="label label-info">IDLE</span>\n' +
    '                    <span ng-switch-when="pass" class="glyphicon glyphicon-ok" style="color:green"></span>\n' +
    '                    <span ng-switch-when="fail" class="glyphicon glyphicon-remove" style="color:red"></span>\n' +
    '                </div>',

        bindings: {
                    status: '<',
                    hideOnIdle: '<'
                  },
        controller: FunSpinnerStatusController
 });