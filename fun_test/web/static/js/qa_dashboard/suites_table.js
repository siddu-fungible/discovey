function SuitesTableController($scope, $http, resultToClass, $window, PagerService) {
    let ctrl = this;

    $scope.resultToClass = function (result) {
        return resultToClass(result);
    };

    ctrl.$onInit = function () {
        $scope.recordsPerPage = 10;
        $scope.logDir = null;
        $scope.suiteExecutionsCount = 0;
        $http.get("/regression/suite_executions_count").then(function(result) {
            $scope.suiteExecutionsCount = (parseInt(result.data));
            $scope.setPage(1);

        });

        if(!$scope.logDir) {
            $http.get("/regression/log_path").then(function (result) {
                $scope.logDir = result.data;
            }).catch(function () {
                $scope.logDir = "/static/logs/s_"
            });
        }

    };


    $scope.setPage = function(page) {
        $scope.pager = PagerService.GetPager($scope.suiteExecutionsCount, page, $scope.recordsPerPage);
        if (page === 0 || (page > $scope.pager.pages.length)) {
            return;
        }
        $http.get("/regression/suite_executions/" + $scope.recordsPerPage + "/" + page).then(function (result) {
            $scope.items = result.data;
        });
    };

    $scope.testCaseLength = function (testCases) {
        return angular.fromJson(testCases).length;
    };

    $scope.getSuiteDetail = function (suiteId) {
        console.log(suiteId);
        $window.location.href = "/regression/suite_detail/" + suiteId;
    };

    $scope.getSchedulerLog = function (suiteId) {
        if($scope.logDir) {
            return $scope.logDir + suiteId + "/scheduler.log"; // TODO
        }

    }
}

function PagerService() {
    // service definition
    let service = {};
    service.GetPager = GetPager;
    return service;

    // service implementation
    function GetPager(totalItems, currentPage, pageSize) {
        // default to first page
        currentPage = currentPage || 1;

        // calculate total pages
        let totalPages = Math.ceil(totalItems / pageSize);

        let startPage, endPage;
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
        let startIndex = (currentPage - 1) * pageSize;
        let endIndex = Math.min(startIndex + pageSize - 1, totalItems - 1);

        // create an array of pages to ng-repeat in the pager control
        let pages = [];
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