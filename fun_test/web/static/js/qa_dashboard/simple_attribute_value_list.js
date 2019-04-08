(function (angular) {
    'use strict';

    function SimpleAttributeValueListController($scope) {
        let ctrl = this;


        ctrl.$onInit = function () {
            console.log(ctrl);
        };

    }

    angular.module('qa-dashboard').component('simpleAttributeValueList', {
        templateUrl: '/static/qa_dashboard/simple_attribute_value_list.html',
        controller: SimpleAttributeValueListController,
        bindings: {
            attributes: '<'
        }
    })

})(window.angular);
