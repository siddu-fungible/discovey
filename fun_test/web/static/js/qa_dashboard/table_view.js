'use strict';


function TableViewController($scope, commonService, pagerService) {

    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        console.log(ctrl.modelName);
        $scope.recordsPerPage = 10;
        $scope.setPage(1);

    };

    $scope.fetchTableData = (pageNumber, recordsPerPage=10) => {
        let payload = {};
        payload["model_name"] = ctrl.modelName;
        let url = "/metrics/table_data" + "/" + pageNumber + "/" + recordsPerPage;
        commonService.apiPost(url, payload).then((data) => {
            $scope.totalCount = data.total_count;
            $scope.headers = data.headers;
            $scope.fields = data.fields;
            $scope.rows = data.data;
        });
    };

    $scope.setPage = function(pageNumber) {
        $scope.pager = pagerService.GetPager($scope.totalCount, pageNumber, $scope.recordsPerPage);
        if (pageNumber === 0 || (pageNumber > $scope.pager.endPage)) {
            return;
        }
        $scope.fetchTableData(pageNumber, $scope.recordsPerPage);
    };

}

angular.module('qa-dashboard').component("tableView", {
        templateUrl: '/static/qa_dashboard/table_view.html',
        bindings: {
                    modelName: '@'
                  },
        controller: TableViewController
 });