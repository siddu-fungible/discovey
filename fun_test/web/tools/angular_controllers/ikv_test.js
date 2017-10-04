(function (angular) {
    'use strict';

    function IkvTestController($scope, $http, uploadService) {
        let ctrl = this;

        $scope.$watch('file', function (newfile, oldfile) {
            if (angular.equals(newfile, oldfile)) {
                return;
            }

            uploadService.upload(newfile).then(function (response) {
                //console.log("result", res);
                $scope.key_hex = response.data;
            })
        });

        ctrl.$onInit = function () {
            $scope.key_hex = null;
        };
    }




    angular.module('tools').component('ikvTest', {
        templateUrl: '/static/ikv_test.html',
        controller: IkvTestController,
        bindings: {}
    })
        .directive("fileinput", [function () {
            return {
                scope: {
                    fileinput: "=",
                    filepreview: "="
                },
                link: function (scope, element, attributes) {
                    element.bind("change", function (changeEvent) {
                        scope.fileinput = changeEvent.target.files[0];
                        let reader = new FileReader();
                        reader.onload = function (loadEvent) {
                            scope.$apply(function () {
                                scope.filepreview = loadEvent.target.result;
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

            function upload(file) {
                let upl = $http({
                    method: 'POST',
                    url: '/tools/tg/ikv_put', // /api/upload
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
        });
})(window.angular);
