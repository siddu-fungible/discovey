(function () {
    let app;
    app = angular.module('qa-dashboard', ['ngSanitize', 'ui.select']);
    app.controller('QaDashBoardController', ['$rootScope', '$scope', '$http', '$window', '$timeout', function ($rootScope, $scope, $http, $window, $timeout) {

        $scope.closeCommonError = function () {
            $rootScope.showCommonError = false;
        };

        $scope.closeCommonSuccess = function () {
            $rootScope.showCommonSuccess = false;
        };

    }]);


    app.factory('resultToClass', [function (result) {
        return function (result) {
            result = result.toUpperCase();
            let klass = "default";
            if (result === "FAILED") {
                klass = "danger";
            } else if (result === "PASSED") {
                klass = "success";
            } else if (result === "SKIPPED") {
                klass = "warning";
            } else if (result === "NOT_RUN") {
                klass = "default";
            } else if (result === "IN_PROGRESS") {
                klass = "info";
            }
            return klass;
        }
    }]);

    app.factory('trimTime', [function (t) {
        return function (t) {
            return t.replace(/\..*$/, "").replace(/T/, " ");
        }
    }]);

    app.factory('commonAlert', ["$rootScope", "$timeout", function ($rootScope, $timeout) {

        function showError(message, timeout) {
            $rootScope.showCommonError = true;
            $rootScope.commonErrorMessage = message;
            let t = 10000;
            if (timeout) {
                t = timeout;
                if (timeout === -1) {
                    t = 1000000;
                }
            }
            $timeout(function() {
                $rootScope.showCommonError = false;
            }, t);
        }

        function showHttpError(message, result, timeout) {
            let errorMessage = message + " :" + result.toString();
            showError(errorMessage, timeout);
        }

        function showSuccess(message, timeout) {
            $rootScope.showCommonSuccess = true;
            $rootScope.commonSuccessMessage = message;
            let t = 10000;
            if (timeout) {
                t = timeout;
                if (timeout === -1) {
                    t = 1000000;
                }
            }
            console.log(t);
            $timeout(function() {
                $rootScope.showCommonSuccess = false;
            }, t)

        }

        function closeAllAlerts() {
            $rootScope.showCommonError = false;
            $rootScope.showCommonSuccess = false;
        }

        return {
            showError: showError,
            showSuccess: showSuccess,
            closeAllAlerts: closeAllAlerts,
            showHttpError: showHttpError,
        };
    }]);
    app.component(funFieldComponent["name"], funFieldComponent["info"]);

}).call();


$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});


