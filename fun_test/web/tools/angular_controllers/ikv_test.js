(function (angular) {
    'use strict';

    function IkvTestController($scope, $http, uploadService, $sce, $timeout) {
        let ctrl = this;

        $scope.$watch('file', function (newfile, oldfile) {
            if (angular.equals(newfile, oldfile)) {
                return;
            }
            $scope.processing = true;
            uploadService.upload(newfile, ctrl.f1, ctrl.topologySessionId, "/tools/tg/ikv_put/").then(function (response) {
                //console.log("result", res);
                $scope.processing = false;
                $scope.keyHex = response.data;
            })
        });
        $scope.$watch('filevideo', function (newfile, oldfile) {
            if (angular.equals(newfile, oldfile)) {
                return;
            }
            $scope.processing = true;
            uploadService.upload(newfile, ctrl.f1, ctrl.topologySessionId, "/tools/tg/ikv_video_put/").then(function (response) {
                //console.log("result", res);
                $scope.keyHex = response.data;
                $scope.getIkvVideoStatus(ctrl.topologySessionId);
            })
        });

        $scope.getIkvVideoStatus = function (sessionId) {
                $http.get("/tools/tg/ikv_video_task_status/" + sessionId.toString()).then(function (result) {
                    status = result.data["status"];
                    if ((status === "NOT_RUN") || (status === "IN_PROGRESS")) {
                        $timeout(function () {
                            $scope.getIkvVideoStatus(sessionId)
                        }, 2000);
                    } else {
                        $scope.processing = false;
                        $scope.playlist = result.data.logs;
                    }
                }).catch(function (result) {
                    alert("Ikv video put status check failed");
                });
        };

        ctrl.$onInit = function () {
            $scope.key_hex = null;
            $scope.processing = null;
        };



        $scope.fetchFile = function () {
            $http.get("/tools/tg/ikv_get/" + $scope.keyHex + "/" + ctrl.topologySessionId + "/" + ctrl.f1.name).then(function (response) {
                console.log(response.data);
                $scope.filepreview = response.data;
                /*
                var myVideo = document.getElementsByTagName('video')[0];
                myVideo.src = $scope.filepreview;
                myVideo.load();
                myVideo.play();*/

            });
        }

    }




    angular.module('tools').component('ikvTest', {
        templateUrl: '/static/ikv_test.html',
        controller: IkvTestController,
        bindings: {
            f1: '=',
            topologySessionId: '='
        }
    })
        .directive("fileinput", [function () {
            return {
                scope: {
                    fileinput: "="
                },
                link: function (scope, element, attributes) {
                    element.bind("change", function (changeEvent) {
                        scope.fileinput = changeEvent.target.files[0];
                        let reader = new FileReader();
                        reader.onload = function (loadEvent) {
                            scope.$apply(function () {
                                //scope.filepreview = loadEvent.target.result;
                            });
                        };
                        reader.readAsDataURL(scope.fileinput);
                    });
                }
            }
        }])
        .service("uploadService", function ($http, $q) {

            return ({
                upload: upload
            });

            function upload(file, f1, sessionId, baseUrl) {
                //$scope.processing = true;
                let upl = $http({
                    method: 'POST',
                    url: baseUrl + sessionId + "/" + f1.name, // /api/upload
                    headers: {
                        'Content-Type': undefined
                    },
                    data: {
                        upload: file
                    },
                    transformRequest: function (data, headersGetter) {
                        let formData = new FormData();
                        angular.forEach(data, function (value, key) {
                            formData.append(key, value);
                        });

                        let headers = headersGetter();
                        delete headers['Content-Type'];

                        return formData;
                    }
                });
                return upl.then(handleSuccess, handleError);

                function handleError(response, data) {
                    if (!angular.isObject(response.data) || !response.data.message) {
                        return ($q.reject("An unknown error occurred."));
                    }

                    return ($q.reject(response.data.message));
                }

                function handleSuccess(response) {
                    return (response);
                }
            }
        })
    .filter("trustUrl", ['$sce', function ($sce) {
        return function (recordingUrl) {
            return $sce.trustAsResourceUrl(recordingUrl);
        };
    }]);
})(window.angular);
