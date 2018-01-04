(function () {
    let app;

    angular
        .module("commonModule", [])
        .filter('propsFilter', function () {
            return function (items, props) {
                let out = [];

                if (angular.isArray(items)) {
                    let keys = Object.keys(props);

                    items.forEach(function (item) {
                        let itemMatches = false;

                        for (let i = 0; i < keys.length; i++) {
                            let prop = keys[i];
                            let text = props[prop].toLowerCase();
                            if (item[prop].toString().toLowerCase().indexOf(text) !== -1) {
                                itemMatches = true;
                                break;
                            }
                        }
                        if (itemMatches) {
                            out.push(item);
                        }
                    });
                } else {
                    // Let the output be the input untouched
                    out = items;
                }
                return out;
            };
        });


    app = angular.module('qa-dashboard', ['ngSanitize', 'ui.select', 'commonModule']);
    app.controller('QaDashBoardController', ['$rootScope', '$scope', '$http', '$window', '$timeout', function ($rootScope, $scope, $http, $window, $timeout) {
        let ctrl = this;

        ctrl.$onInit = function () {

        };

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

    app.factory('commonService', ["$rootScope", "$timeout", "$http", function ($rootScope, $timeout, $http) {
        function validateApiResult (apiResult, message) {
            let result = false;
            let data = apiResult["data"];
            if (!data["status"]) {
                showError(message, 10 * 1000, data);
            } else {
                result = true;
            }
            return result;
        }

        function addLogEntry (log, details) {
            let payload = {};
            payload["log"] = log;
            payload["time"] = new Date();
            if(details) {
                payload["details"] = details;
            } else {
                payload["details"] = "";
            }
            $http.post("/common/add_session_log", payload).then(function () {

            });
        }

        function showError (message, timeout, result) {
            $rootScope.showCommonError = true;
            let stack = null;
            if(result) {
                if(result.stack) {
                    stack = result.stack;
                }
                else {
                    try {
                        throw new Error();
                    } catch(e) {
                        stack = e.stack;
                    }
                }
            } else {
                try {
                    throw new Error();
                } catch(e) {
                    stack = e.stack.replace(/\n/, '<br>').replace("&#10", "<br>");
                }
            }

            let detailedMessage = "";
            if(result.error_message) {
                detailedMessage = "Error Message: " + result.error_message;
            }
            detailedMessage += "\n" + stack;
            addLogEntry(message, detailedMessage);

            $rootScope.commonErrorMessage = message;
            let t = 10000;
            if (timeout) {
                t = timeout;
                if (timeout === -1) {
                    t = 1000000;
                }
            }
            $timeout(function () {
                $rootScope.showCommonError = false;
            }, t);
        }

        function showHttpError (message, result, timeout) {
            let errorMessage = result;
            if (result.data) {
                errorMessage = result.data;
            }
            addLogEntry(message, errorMessage);
            showError(message, timeout, result);
        }

        function showSuccess (message, timeout) {
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
            $timeout(function () {
                $rootScope.showCommonSuccess = false;
            }, t)

        }

        function closeAllAlerts () {
            $rootScope.showCommonError = false;
            $rootScope.showCommonSuccess = false;
        }

        function apiGet (url, message) {
            return $http.get(url).then(function (result) {
                let data = null;
                if (validateApiResult(result, message)) {
                    data = result.data.data;
                }
                return data;
            }).catch(function (result) {
                showHttpError(message, result);
            });

        }

        function apiPost (url, payload, message) {
            return $http.post(url, payload).then(function (result) {
                let data = null;
                if (validateApiResult(result, message)) {
                    data = result.data.data;
                }
                return data;
            }).catch(function(result){
                showHttpError(message, result);
            });
        }

        return {
            showError: showError,
            showSuccess: showSuccess,
            closeAllAlerts: closeAllAlerts,
            showHttpError: showHttpError,
            validateApiResult: validateApiResult,
            apiGet: apiGet,
            apiPost: apiPost,
            addLogEntry: addLogEntry
        };

    }]);

    app.component(funFieldComponent["name"], funFieldComponent["info"]);
    app.component(funSpinnerStatusComponent["name"], funSpinnerStatusComponent["info"]);

}).call();


$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});


