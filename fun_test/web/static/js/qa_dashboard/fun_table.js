'use strict';


function FunTableController($scope, pagerService) {
    let ctrl = this;
    this.$onInit = function () {
        $scope.headers = ctrl.headers;
        $scope.data = ctrl.data;
        $scope.filterDataSets = ctrl.filterDataSets;
        $scope.totalCount = null;
        $scope.recordsPerPage = 10;
        $scope.allData = $scope.data;
        $scope.setPage(1);
    };

    $scope.cleanValue = (key, value) => {
        try {
            if (key === "input_date_time") {
                //return ctrl.xaxisFormatter()(value);
                let s = "Error";
                let r = /(\d{4})-(\d{2})-(\d{2})/g;
                let match = r.exec(value);
                if (match) {
                    s = match[2] + "/" + match[3];
                }
                return s;
            } else {
                return value;
            }
        } catch (e) {

        }

    };

    $scope.$watch(
        () => {
            return [ctrl.data, ctrl.filterDataSets];
        }, function (newvalue, oldvalue) {
            if (newvalue === oldvalue) {
                // console.log(newvalue, oldvalue);
                return;
            }
            $scope.headers = ctrl.headers;
            $scope.data = ctrl.data;
            $scope.allData = $scope.data;
            $scope.filterDataSets = ctrl.filterDataSets;
            $scope.setPage(1);
    }, true);

    $scope.isFieldRelevant = (fieldName) => {
        let relevant = false;
        if (fieldName === "input_date_time") {
            relevant = true;
        }
        $scope.filterDataSets.forEach((oneDataSet) => {
            angular.forEach(oneDataSet.inputs, (value, key) => {
                if (key === fieldName) {
                    relevant = true;
                }
            });
            if (fieldName === oneDataSet.output.name) {
                relevant = true;
            }
        });
        return relevant;
    };

    $scope.setPage = function(pageNumber) {

        let start = ( pageNumber - 1 ) * $scope.recordsPerPage;
        let end = pageNumber * $scope.recordsPerPage;
        let multipleTableData = [];
        for(let j = 0; j < $scope.allData.length; j++) {
            let pageData = [];
            $scope.totalCount = $scope.allData[j].length;
            $scope.pager = pagerService.GetPager($scope.totalCount, pageNumber, $scope.recordsPerPage);
            if (pageNumber === 0 || (pageNumber > $scope.pager.endPage)) {
                return;
            }
            for(let i = start; i < end && i < $scope.totalCount; i++)
            {
                pageData.push($scope.allData[j][i]);
            }
            multipleTableData.push(pageData);
        }
        $scope.data = multipleTableData;
    };

}

angular.module('qa-dashboard').component("funTable", {
        templateUrl: '/static/qa_dashboard/fun_table.html',
        bindings: {
                    headers: '<',
                    data: '<',
                    filterDataSets: '<'
                  },
        controller: FunTableController
 });