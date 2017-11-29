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

    app.factory('commonAlert', ["$rootScope", function ($rootScope) {
        function showError(message) {
            $rootScope.showCommonError = true;
            $rootScope.commonErrorMessage = message;
        }

        function showSuccess(message) {
            $rootScope.showCommonSuccess = true;
            $rootScope.commonSuccessMessage = message;
        }

        function closeAllAlerts() {
            $rootScope.showCommonError = false;
            $rootScope.showCommonSuccess = false;
        }

        return {
            showError: showError,
            showSuccess: showSuccess,
            closeAllAlerts: closeAllAlerts
        };
    }]);
    app.component(funFieldComponent["name"], funFieldComponent["info"]);

}).call();


$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});


