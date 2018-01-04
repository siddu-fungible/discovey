'use strict';


let regressionSanitySummaryInfo = {
    template: ' <div class="panel panel-primary" style="max-height: 500px; min-height: 500px">\n' +
    '               <div class="panel-heading">Regression Sanity</div>\n' +
    '                   <div class="panel-body"> '+
    '                       <fun-spinner-status status="status" hide-on-idle="true"></fun-spinner-status>\n' +
    '                       <table class="table table-nonfluid table-borderless">\n' +
    '                            <tr>\n' +
    '                                <td>Hourly Sanity</td>\n' +
    '                                <td><label class="label label-{{ getColorForResult(hourlySanity) }}">{{hourlySanity}}</label></td>\n' +
    '                            </tr>\n' +
    '                            <tr>\n' +
    '                                <td>Nightly Sanity</td>\n' +
    '                                <td><label class="label label-{{ getColorForResult(nightlySanity) }}">{{nightlySanity}}</label></td>\n' +
    '                            </tr>\n' +
    '                       </table>\n' +
    '                   </div>\n' +
    '               </div>\n' +
    '            </div>',

    controller: RegressionSanitySummaryController
};


function RegressionSanitySummaryController($scope, $http, commonService) {
    let ctrl = this;

    ctrl.$onInit = function () {
        $scope.status = "idle";
        $scope.fetchRegressionSanity();
        $scope.hourlySanity = "UNKNOWN";
        $scope.nightlySanity = "UNKNOWN";
    };

    $scope.fetchRegressionSanity = function () {
        $http.get('/regression/last_jenkins_hourly_execution_status').then(function (result){
            $scope.hourlySanity = result.data;
        }).catch(function (result) {
            commonService.showError("fetchRegressionSanity", 10000, result);
        })

    };

    $scope.getColorForResult = function (result) {
        return commonService.getColorForResult(result);
    };
}

let regressionSanitySummaryComponent = {"name": "regressionSanitySummary", "info": regressionSanitySummaryInfo};

