(function () {
    let app;
    app = angular.module('qa-dashboard', []);
    app.controller('QaDashBoardController', ['$scope', '$http', '$window', '$timeout', function ($scope, $http, $window, $timeout) {
    }]);
    app.factory('resultToButtonClass', [function (result) {
        return function (result) {
            result = result.toUpperCase();
            let buttonClass = "btn-default";
            if (result === "FAILED") {
                buttonClass = "btn-danger";
            } else if (result === "PASSED") {
                buttonClass = "btn-success"
            } else if (result === "SKIPPED") {
                buttonClass = "btn-warning"
            } else if (result === "NOT_RUN") {
                buttonClass = "btn-info"
            }
            return buttonClass;
        }
    }]);
}).call();


$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});


