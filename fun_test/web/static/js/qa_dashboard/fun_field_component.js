let funFieldComponentInfo = {

        template: "<div class='{{ $ctrl.klass }}'>" +
                  "<input style='width: 100%' type='{{ $ctrl.type }}' ng-model='value' ng-change='onChange()'/>" +
                  "<p ng-if='!value && $ctrl.required' style='{{ errorStyle }}'>{{ $ctrl.type }} * Required</p>" +
                  "<p ng-show='minRequirementError' style='{{ errorStyle }}'>{{ minRequirementError }}</p>" +
                  "<p ng-show='maxRequirementError' style='{{ errorStyle }}'>{{ maxRequirementError }}</p>" +
                  "<p ng-show='minLengthRequirementError' style='{{ errorStyle }}'>{{ minLengthRequirementError }}</p>" +
                  "<p ng-show='maxLengthRequirementError' style='{{ errorStyle }}'>{{ maxLengthRequirementError }}</p>" +
                  "</div>",

        bindings: {
                    type: '@',
                    min: '<',
                    max: '<',
                    minLength: '<',
                    maxLength: '<',
                    required: '@',
                    klass: '@',
                    bindValue: '='
                  },
        controller: FunFieldController
 };



let funFieldComponent = {"name": "funField", "info": funFieldComponentInfo};



function FunFieldController($scope, commonService) {
    let ctrl = this;

    this.$onInit = function () {
        console.log(ctrl);
        $scope.requiredError = false;
        $scope.minRequirementError = null;
        $scope.maxRequirementError = null;
        $scope.minLengthRequirementError = null;
        $scope.maxLengthRequirementError = null;
        $scope.errorStyle = "color: #a94442";

    };

    $scope.testClick = function () {
        console.log("testClick");
        console.log(ctrl.f);

    };

    $scope.onChange = function () {
        ctrl.bindValue = $scope.value;
        if(ctrl.type === "number") {
            let result = validateNumber();
        } else if(ctrl.type === "text") {
            let result = validateText();
        }
        commonService.closeAllAlerts();
    };

    let validateNumber = function () {
        $scope.minRequirementError = null;
        $scope.maxRequirementError = null;

        let result = true;
        if(ctrl.min) {
            if($scope.value < ctrl.min) {
                $scope.minRequirementError = "Value is less than: " + ctrl.min;
                result = false;
            }
        }
        if(ctrl.max) {
            if($scope.value > ctrl.max) {
                $scope.minRequirementError = "Value is greater than: " + ctrl.max;
                result = false;
            }
        }
        if (!result) {
            console.log($scope.value + " : is invalid");
            $scope.value = null;
        }
        else {
            console.log($scope.value + " : is valid");
        }
        return result
    };

    let validateText = function () {
        $scope.minLengthRequirementError = null;
        $scope.maxLengthRequirementError = null;

        let result = true;
        if(ctrl.minLength) {
            if($scope.value.length < ctrl.minLength) {
                $scope.minLengthRequirementError = "Length of value is less than: " + ctrl.minLength;
                result = false;
            }
        }
        if(ctrl.maxLength) {
            if($scope.value.length > ctrl.maxLength) {
                $scope.maxLengthRequirementError = "Length of value is greater than: " + ctrl.maxLength;
                result = false;
            }
        }
        if (!result) {
            console.log($scope.value + " : is invalid");
        }
        else {
            console.log($scope.value + " : is valid");
        }
        return result
    }




}
