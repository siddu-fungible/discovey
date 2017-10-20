function SuitesTableController($scope, $http, resultToClass, $window, PagerService) {
    let ctrl = this;

    $scope.resultToClass = function (result) {
        return resultToClass(result);
    };

    ctrl.$onInit = function () {
        //console.log(ctrl);




        function initController() {
            // initialize to page 1
            ctrl.setPage(1);
            let i = 0;
        }

        $scope.suite_executions = null;
        $http.get("/regression/suite_executions").then(function (result) {
            $scope.suiteExecutions = result.data; // TODO: validate
            ctrl.dummyItems = $scope.suiteExecutions;
            ctrl.pager = {};
            ctrl.setPage = setPage;
            initController();


        });
    };


    function setPage(page) {
        if (page < 0 || page > ctrl.pager.totalPages) {
            return;
        }

        ctrl.pager = PagerService.GetPager(ctrl.dummyItems.length, page);

        ctrl.items = ctrl.dummyItems.slice(ctrl.pager.startIndex, ctrl.pager.endIndex + 1);
    }

    $scope.testCaseLength = function (testCases) {
        return angular.fromJson(testCases).length;
    };

    $scope.getSuiteDetail = function (suiteId) {
        console.log(suiteId);
        $window.location.href = "/regression/suite_detail/" + suiteId;
    };


}


function PagerService() {
    // service definition
    var service = {};

    service.GetPager = GetPager;

    return service;

    // service implementation
    function GetPager(totalItems, currentPage, pageSize) {
        // default to first page
        currentPage = currentPage || 1;

        // default page size is 10
        pageSize = pageSize || 10;

        // calculate total pages
        var totalPages = Math.ceil(totalItems / pageSize);

        var startPage, endPage;
        if (totalPages <= 10) {
            // less than 10 total pages so show all
            startPage = 1;
            endPage = totalPages;
        } else {
            // more than 10 total pages so calculate start and end pages
            if (currentPage <= 6) {
                startPage = 1;
                endPage = 10;
            } else if (currentPage + 4 >= totalPages) {
                startPage = totalPages - 9;
                endPage = totalPages;
            } else {
                startPage = currentPage - 5;
                endPage = currentPage + 4;
            }
        }

        // calculate start and end item indexes
        var startIndex = (currentPage - 1) * pageSize;
        var endIndex = Math.min(startIndex + pageSize - 1, totalItems - 1);

        // create an array of pages to ng-repeat in the pager control
        var pages = [];
        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }

        // return object with all pager properties required by the view
        return {
            totalItems: totalItems,
            currentPage: currentPage,
            pageSize: pageSize,
            totalPages: totalPages,
            startPage: startPage,
            endPage: endPage,
            startIndex: startIndex,
            endIndex: endIndex,
            pages: pages
        };
    }
}

angular.module('qa-dashboard')
    .component('suitesTable', {
        templateUrl: '/static/qa_dashboard/suites_table.html',
        controller: SuitesTableController,
        bindings: {}
    })
    .factory('PagerService', PagerService);