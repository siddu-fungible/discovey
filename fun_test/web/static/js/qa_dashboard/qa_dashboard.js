(function () {
    let app;
    app = angular.module('qa-dashboard', []);
    app.controller('QaDashBoardController', ['$scope', '$http', '$window', '$timeout', function ($scope, $http, $window, $timeout) {
    }]);
    app.factory('resultToClass', [function (result) {
        return function (result) {
            result = result.toUpperCase();
            let klass = "default";
            if (result === "FAILED") {
                klass = "danger";
            } else if (result === "PASSED") {
                klass = "success"
            } else if (result === "SKIPPED") {
                klass = "warning"
            } else if (result === "NOT_RUN") {
                klass = "info"
            }
            return klass;
        }
    }]);
}).call();


$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});


