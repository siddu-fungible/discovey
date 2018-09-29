(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["main"],{

/***/ "./src/$$_lazy_route_resource lazy recursive":
/*!**********************************************************!*\
  !*** ./src/$$_lazy_route_resource lazy namespace object ***!
  \**********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

function webpackEmptyAsyncContext(req) {
	// Here Promise.resolve().then() is used instead of new Promise() to prevent
	// uncaught exception popping up in devtools
	return Promise.resolve().then(function() {
		var e = new Error("Cannot find module '" + req + "'");
		e.code = 'MODULE_NOT_FOUND';
		throw e;
	});
}
webpackEmptyAsyncContext.keys = function() { return []; };
webpackEmptyAsyncContext.resolve = webpackEmptyAsyncContext;
module.exports = webpackEmptyAsyncContext;
webpackEmptyAsyncContext.id = "./src/$$_lazy_route_resource lazy recursive";

/***/ }),

/***/ "./src/app/app-routing.module.ts":
/*!***************************************!*\
  !*** ./src/app/app-routing.module.ts ***!
  \***************************************/
/*! exports provided: AppRoutingModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppRoutingModule", function() { return AppRoutingModule; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _dashboard_dashboard_component__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./dashboard/dashboard.component */ "./src/app/dashboard/dashboard.component.ts");
/* harmony import */ var _performance_performance_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./performance/performance.component */ "./src/app/performance/performance.component.ts");
/* harmony import */ var _test_test_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./test/test.component */ "./src/app/test/test.component.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};





var routes = [
    { path: 'upgrade', component: _dashboard_dashboard_component__WEBPACK_IMPORTED_MODULE_2__["DashboardComponent"] },
    { path: 'upgrade/dashboard', component: _dashboard_dashboard_component__WEBPACK_IMPORTED_MODULE_2__["DashboardComponent"] },
    { path: 'upgrade/performance', component: _performance_performance_component__WEBPACK_IMPORTED_MODULE_3__["PerformanceComponent"] },
    { path: 'upgrade/test', component: _test_test_component__WEBPACK_IMPORTED_MODULE_4__["TestComponent"] }
];
var AppRoutingModule = /** @class */ (function () {
    function AppRoutingModule() {
    }
    AppRoutingModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["NgModule"])({
            imports: [_angular_router__WEBPACK_IMPORTED_MODULE_1__["RouterModule"].forRoot(routes)],
            exports: [_angular_router__WEBPACK_IMPORTED_MODULE_1__["RouterModule"]]
        })
    ], AppRoutingModule);
    return AppRoutingModule;
}());



/***/ }),

/***/ "./src/app/app.component.css":
/*!***********************************!*\
  !*** ./src/app/app.component.css ***!
  \***********************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/app.component.html":
/*!************************************!*\
  !*** ./src/app/app.component.html ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<!DOCTYPE html>\n<html lang=\"en\" ng-app=\"qa-dashboard\">\n<head>\n    <title>QA Dashboard</title>\n\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n\n    <!-- css -->\n    <!-- link href=\"static/css/common/bootstrap.min.css\"  rel=\"stylesheet\" id=\"bootstrap-css\" -->\n\n</head>\n<body>\n  <h1>QA Dashboard</h1>\n\n<!--div class=\"nav-side-menu\" style=\"width: 10%\">\n    <div class=\"brand\">Fungible QA</div>\n    <i class=\"fa fa-bars fa-2x toggle-btn\" data-toggle=\"collapse\" data-target=\"#menu-content\"></i>\n    <div class=\"menu-list\">\n        <ul id=\"menu-content\" class=\"menu-content collapse out\">\n            <li data-toggle=\"collapse\" data-target=\"#regression-tasks\">\n                <a href=\"#\"><i class=\"fa fa-dashboard fa-lg\"></i>Regression<span class=\"arrow\"></span></a>\n            </li>\n            <ul class=\"sub-menu\" id=\"regression-tasks\">\n                <li class=\"active\"><a href=\"/regression\">All Jobs</a></li>\n                <li class=\"active\"><a href=\"/regression/completed_jobs\">Completed Jobs</a></li>\n                <li class=\"active\"><a href=\"/regression/pending_jobs\">Pending Jobs</a></li>\n                <li class=\"active\"><a href=\"/regression/jenkins_jobs\">Jenkins Jobs</a></li>\n                <li><a href=\"/regression/submit_job_page\">Submit Jobs</a></li>\n            </ul>\n            <li data-toggle=\"collapse\" data-target=\"#test-case\" class=\"collapsed\">\n                <a href=\"#\"><i class=\"fa fa-globe fa-lg\"></i> Test-cases <span class=\"arrow\"></span></a>\n            </li>\n            <ul class=\"sub-menu collapse\" id=\"test-case\">\n                <li><a href=\"/tcm/view_catalog_page\">View Catalog</a></li>\n                <li><a href=\"/tcm/create_catalog_page\">Create Catalog</a></li>\n            </ul>\n        </ul>\n    </div>\n</div-->\n\n<nav class=\"navbar navbar-default\" style=\"background-color: #337ab7;\">\n    <div class=\"container-fluid\">\n        <!-- Brand and toggle get grouped for better mobile display -->\n        <div class=\"navbar-header\">\n            <button type=\"button\" class=\"navbar-toggle collapsed\" data-toggle=\"collapse\"\n                    data-target=\"#qa-dashboard-navbar\" aria-expanded=\"false\">\n                <span class=\"sr-only\">Toggle navigation</span>\n                <span class=\"icon-bar\"></span>\n                <span class=\"icon-bar\"></span>\n                <span class=\"icon-bar\"></span>\n            </button>\n            <a class=\"navbar-brand\" href=\"/\" style=\"color: white\">Integration</a>\n        </div>\n\n        <!-- Collect the nav links, forms, and other content for toggling -->\n        <div class=\"collapse navbar-collapse\" id=\"qa-dashboard-navbar\">\n            <ul class=\"nav navbar-nav\">\n                <li>\n                    <a href=\"/upgrade/performance\" style=\"color: white;background-color: #337ab7\" role=\"button\">Performance</a>\n                </li>\n\n                <li class=\"dropdown\">\n                    <a href=\"/common/home\" style=\"color: white;background-color: #337ab7\" class=\"dropdown-toggle\" data-toggle=\"dropdown\" role=\"button\" aria-haspopup=\"true\"\n                       aria-expanded=\"false\">Regression<span class=\"caret\"></span></a>\n                    <ul class=\"dropdown-menu\">\n                        <li><a href=\"/regression\">All Jobs</a></li>\n                        <li><a href=\"/regression/completed_jobs\">Completed Jobs</a></li>\n                        <li><a href=\"/regression/pending_jobs\">Pending Jobs</a></li>\n                        <li><a href=\"/regression/submit_job_page\">Submit Job</a></li>\n                        <li role=\"separator\" class=\"divider\"></li>\n                        <li><a href=\"/regression/jenkins_jobs\">Jenkins Jobs</a></li>\n                        <li><a href=\"/regression/jobs_by_tag/network-sanity\">Networking Sanity</a></li>\n                        <li><a href=\"/metrics/atomic/Unit-Tests/UnitTestPerformance\">FunOS Unit-Tests</a></li>\n                    </ul>\n                </li>\n                <li class=\"dropdown\">\n                    <a href=\"#\" class=\"dropdown-toggle\" data-toggle=\"dropdown\" role=\"button\" aria-haspopup=\"true\"\n                       aria-expanded=\"false\" style=\"color: white;background-color: #337ab7\">Test-cases<span class=\"caret\"></span></a>\n                    <ul class=\"dropdown-menu\">\n                        <li><a href=\"/tcm/releases_page\">Releases</a> </li>\n                        <li><a href=\"/tcm/view_catalogs\">View Catalogs</a></li>\n                        <li><a href=\"/tcm/create_catalog_page\">Create Catalog</a></li>\n                    </ul>\n                </li>\n                <li class=\"dropdown\">\n                    <a href=\"#\" style=\"color: white;background-color: #337ab7\" class=\"dropdown-toggle\" data-toggle=\"dropdown\" role=\"button\" aria-haspopup=\"true\"\n                       aria-expanded=\"false\">Administration<span class=\"caret\"></span></a>\n                    <ul class=\"dropdown-menu\">\n                        <li><a href=\"/metrics\">All</a> </li>\n                        <li><a href=\"/metrics/summary\">Summary</a></li>\n                        <li><a href=\"/initialize\">Initialize</a></li>\n                    </ul>\n                </li>\n            </ul>\n            <!--form class=\"navbar-form navbar-left\">\n                <div class=\"form-group\">\n                    <input type=\"text\" class=\"form-control\" placeholder=\"Search\">\n                </div>\n                <button type=\"submit\" class=\"btn btn-default\">Submit</button>\n            </form-->\n            <ul class=\"nav navbar-nav navbar-right\">\n                <li><a href=\"/common/alerts_page\" role=\"button\" style=\"color: white;background-color: #337ab7\">Alerts</a></li>\n            </ul>\n        </div><!-- /.navbar-collapse -->\n    </div><!-- /.container-fluid -->\n</nav>\n\n<div class=\"content\" ng-controller=\"QaDashBoardController\" ng-if=\"showCommonError\">\n    <div class=\"alert alert-danger alert-dismissible show\" role=\"alert\">\n        <strong>{{ commonErrorMessage }} </strong>&nbsp <a href=\"{{ commonAlertLink }}\">Details</a> {{ detailError }}\n        <button type=\"button\" class=\"close\" aria-label=\"Close\">\n            <span aria-hidden=\"true\" ng-click=\"closeCommonError()\">&times;</span>\n        </button>\n    </div>\n</div>\n<div class=\"content\" ng-controller=\"QaDashBoardController\" ng-if=\"showCommonSuccess\">\n    <div class=\"alert alert-success alert-dismissible show\" role=\"alert\">\n        <strong>{{ commonSuccessMessage }}</strong>\n        <button type=\"button\" class=\"close\" aria-label=\"Close\">\n            <span aria-hidden=\"true\" ng-click=\"closeCommonSuccess()\">&times;</span>\n        </button>\n    </div>\n</div>\n\n\n<router-outlet></router-outlet>\n\n\n</body>\n</html>\n\n\n"

/***/ }),

/***/ "./src/app/app.component.ts":
/*!**********************************!*\
  !*** ./src/app/app.component.ts ***!
  \**********************************/
/*! exports provided: AppComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppComponent", function() { return AppComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};

var AppComponent = /** @class */ (function () {
    function AppComponent() {
        this.title = 'qadashboard';
    }
    AppComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-root',
            template: __webpack_require__(/*! ./app.component.html */ "./src/app/app.component.html"),
            styles: [__webpack_require__(/*! ./app.component.css */ "./src/app/app.component.css")]
        })
    ], AppComponent);
    return AppComponent;
}());



/***/ }),

/***/ "./src/app/app.module.ts":
/*!*******************************!*\
  !*** ./src/app/app.module.ts ***!
  \*******************************/
/*! exports provided: AppModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppModule", function() { return AppModule; });
/* harmony import */ var _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/platform-browser */ "./node_modules/@angular/platform-browser/fesm5/platform-browser.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_material__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/material */ "./node_modules/@angular/material/esm5/material.es5.js");
/* harmony import */ var _angular_platform_browser_animations__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/platform-browser/animations */ "./node_modules/@angular/platform-browser/fesm5/animations.js");
/* harmony import */ var _app_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./app.component */ "./src/app/app.component.ts");
/* harmony import */ var _dashboard_dashboard_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./dashboard/dashboard.component */ "./src/app/dashboard/dashboard.component.ts");
/* harmony import */ var _app_routing_module__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./app-routing.module */ "./src/app/app-routing.module.ts");
/* harmony import */ var _performance_performance_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./performance/performance.component */ "./src/app/performance/performance.component.ts");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var _fun_table_fun_table_component__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./fun-table/fun-table.component */ "./src/app/fun-table/fun-table.component.ts");
/* harmony import */ var _services_api_api_service__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./services/api/api.service */ "./src/app/services/api/api.service.ts");
/* harmony import */ var _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./services/logger/logger.service */ "./src/app/services/logger/logger.service.ts");
/* harmony import */ var _test_test_component__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(/*! ./test/test.component */ "./src/app/test/test.component.ts");
/* harmony import */ var _pipe_fun_table_filter_pipe__WEBPACK_IMPORTED_MODULE_13__ = __webpack_require__(/*! ./pipe/fun-table-filter.pipe */ "./src/app/pipe/fun-table-filter.pipe.ts");
/* harmony import */ var _chart_chart_component__WEBPACK_IMPORTED_MODULE_14__ = __webpack_require__(/*! ./chart/chart.component */ "./src/app/chart/chart.component.ts");
/* harmony import */ var _fun_chart_fun_chart_component__WEBPACK_IMPORTED_MODULE_15__ = __webpack_require__(/*! ./fun-chart/fun-chart.component */ "./src/app/fun-chart/fun-chart.component.ts");
/* harmony import */ var angular_highcharts__WEBPACK_IMPORTED_MODULE_16__ = __webpack_require__(/*! angular-highcharts */ "./node_modules/angular-highcharts/angular-highcharts.es5.js");
/* harmony import */ var _fun_metric_chart_fun_metric_chart_component__WEBPACK_IMPORTED_MODULE_17__ = __webpack_require__(/*! ./fun-metric-chart/fun-metric-chart.component */ "./src/app/fun-metric-chart/fun-metric-chart.component.ts");
/* harmony import */ var angular_font_awesome__WEBPACK_IMPORTED_MODULE_18__ = __webpack_require__(/*! angular-font-awesome */ "./node_modules/angular-font-awesome/dist/angular-font-awesome.es5.js");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_19__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm5/forms.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};




















var AppModule = /** @class */ (function () {
    function AppModule() {
    }
    AppModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
            declarations: [
                _app_component__WEBPACK_IMPORTED_MODULE_4__["AppComponent"],
                _dashboard_dashboard_component__WEBPACK_IMPORTED_MODULE_5__["DashboardComponent"],
                _performance_performance_component__WEBPACK_IMPORTED_MODULE_7__["PerformanceComponent"],
                _fun_table_fun_table_component__WEBPACK_IMPORTED_MODULE_9__["FunTableComponent"],
                _test_test_component__WEBPACK_IMPORTED_MODULE_12__["TestComponent"],
                _pipe_fun_table_filter_pipe__WEBPACK_IMPORTED_MODULE_13__["FunTableFilterPipe"],
                _chart_chart_component__WEBPACK_IMPORTED_MODULE_14__["ChartComponent"],
                _fun_chart_fun_chart_component__WEBPACK_IMPORTED_MODULE_15__["FunChartComponent"],
                _fun_metric_chart_fun_metric_chart_component__WEBPACK_IMPORTED_MODULE_17__["FunMetricChartComponent"]
            ],
            imports: [
                _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__["BrowserModule"],
                _angular_common_http__WEBPACK_IMPORTED_MODULE_8__["HttpClientModule"],
                _app_routing_module__WEBPACK_IMPORTED_MODULE_6__["AppRoutingModule"],
                _angular_platform_browser_animations__WEBPACK_IMPORTED_MODULE_3__["BrowserAnimationsModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_2__["MatSortModule"],
                angular_highcharts__WEBPACK_IMPORTED_MODULE_16__["ChartModule"],
                angular_font_awesome__WEBPACK_IMPORTED_MODULE_18__["AngularFontAwesomeModule"],
                _angular_forms__WEBPACK_IMPORTED_MODULE_19__["FormsModule"]
            ],
            providers: [_services_api_api_service__WEBPACK_IMPORTED_MODULE_10__["ApiService"], _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_11__["LoggerService"]],
            bootstrap: [_app_component__WEBPACK_IMPORTED_MODULE_4__["AppComponent"]]
        })
    ], AppModule);
    return AppModule;
}());



/***/ }),

/***/ "./src/app/chart/chart.component.ts":
/*!******************************************!*\
  !*** ./src/app/chart/chart.component.ts ***!
  \******************************************/
/*! exports provided: ChartComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ChartComponent", function() { return ChartComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var angular_highcharts__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! angular-highcharts */ "./node_modules/angular-highcharts/angular-highcharts.es5.js");
/* harmony import */ var _services_api_api_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../services/api/api.service */ "./src/app/services/api/api.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (undefined && undefined.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = y[op[0] & 2 ? "return" : op[0] ? "throw" : "next"]) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [0, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};



var ChartComponent = /** @class */ (function () {
    function ChartComponent(apiService) {
        this.apiService = apiService;
        this.chart = new angular_highcharts__WEBPACK_IMPORTED_MODULE_1__["Chart"]({
            chart: {
                type: 'line'
            },
            title: {
                text: 'Linechart'
            },
            credits: {
                enabled: false
            },
            series: [
                {
                    name: 'Line 1',
                    data: [1, 2, 3]
                }
            ]
        });
    }
    ChartComponent.prototype.ngOnInit = function () {
        // this.doSomething1();
    };
    ChartComponent.prototype.doSomething1 = function () {
        var _this = this;
        console.log("Doing Something1");
        var payload = { "metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"] };
        this.apiService.post('/metrics/scores', payload).subscribe(function (response) {
            console.log(response.data);
            _this.delay(1000);
        }, function (error) {
            console.log(error);
            _this.delay(1000);
        });
    };
    ChartComponent.prototype.delay = function (ms) {
        return __awaiter(this, void 0, void 0, function () {
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(function () { return resolve(); }, ms); }).then(function () {
                            _this.add();
                            _this.doSomething1();
                            console.log("fired");
                        })];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    ChartComponent.prototype.r = function () {
        return Math.random();
    };
    // add point to chart serie
    ChartComponent.prototype.add = function () {
        this.chart.addPoint(Math.floor(Math.random() * 10));
    };
    ChartComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-fun-chart',
            template: "\n    <button (click)=\"add()\">Add Point!</button>\n    <!--div [chart]=\"chart\"></div-->\n  "
        }),
        __metadata("design:paramtypes", [_services_api_api_service__WEBPACK_IMPORTED_MODULE_2__["ApiService"]])
    ], ChartComponent);
    return ChartComponent;
}());



/***/ }),

/***/ "./src/app/dashboard/dashboard.component.css":
/*!***************************************************!*\
  !*** ./src/app/dashboard/dashboard.component.css ***!
  \***************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/dashboard/dashboard.component.html":
/*!****************************************************!*\
  !*** ./src/app/dashboard/dashboard.component.html ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div>\n  My dashboard\n  <app-performance></app-performance>\n  <app-test></app-test>\n</div>\n"

/***/ }),

/***/ "./src/app/dashboard/dashboard.component.ts":
/*!**************************************************!*\
  !*** ./src/app/dashboard/dashboard.component.ts ***!
  \**************************************************/
/*! exports provided: DashboardComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "DashboardComponent", function() { return DashboardComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var DashboardComponent = /** @class */ (function () {
    function DashboardComponent() {
    }
    DashboardComponent.prototype.ngOnInit = function () {
    };
    DashboardComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-dashboard',
            template: __webpack_require__(/*! ./dashboard.component.html */ "./src/app/dashboard/dashboard.component.html"),
            styles: [__webpack_require__(/*! ./dashboard.component.css */ "./src/app/dashboard/dashboard.component.css")]
        }),
        __metadata("design:paramtypes", [])
    ], DashboardComponent);
    return DashboardComponent;
}());



/***/ }),

/***/ "./src/app/fun-chart/fun-chart.component.css":
/*!***************************************************!*\
  !*** ./src/app/fun-chart/fun-chart.component.css ***!
  \***************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/fun-chart/fun-chart.component.html":
/*!****************************************************!*\
  !*** ./src/app/fun-chart/fun-chart.component.html ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<p>\n  fun-chart works!\n</p>\n<button (click)=\"add()\">Add Point!</button>\n    <div [chart]=\"chart\"></div>\n"

/***/ }),

/***/ "./src/app/fun-chart/fun-chart.component.ts":
/*!**************************************************!*\
  !*** ./src/app/fun-chart/fun-chart.component.ts ***!
  \**************************************************/
/*! exports provided: FunChartComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "FunChartComponent", function() { return FunChartComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var angular_highcharts__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! angular-highcharts */ "./node_modules/angular-highcharts/angular-highcharts.es5.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


var FunChartComponent = /** @class */ (function () {
    function FunChartComponent() {
    }
    // @Input() xValues: any[];
    // @Input() yValues: any[];
    FunChartComponent.prototype.add = function () {
        this.chart.addPoint(Math.floor(Math.random() * 10));
    };
    FunChartComponent.prototype.ngOnChanges = function () {
        this.chart = new angular_highcharts__WEBPACK_IMPORTED_MODULE_1__["Chart"]({
            chart: {
                type: 'line',
                width: 500,
                height: 500
            },
            title: {
                text: this.title
            },
            xAxis: {
                title: {
                    text: this.xAxisLabel
                }
            },
            yAxis: {
                title: {
                    text: this.y1AxisLabel
                }
            },
            credits: {
                enabled: false
            },
            plotOptions: {
                line: {
                    animation: false,
                    marker: {
                        enabled: true
                    }
                },
                series: {
                    animation: false
                }
            },
            series: this.y1Values
        });
    };
    FunChartComponent.prototype.ngOnInit = function () {
    };
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", Array)
    ], FunChartComponent.prototype, "y1Values", void 0);
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", Array)
    ], FunChartComponent.prototype, "xValues", void 0);
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", String)
    ], FunChartComponent.prototype, "title", void 0);
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", String)
    ], FunChartComponent.prototype, "xAxisLabel", void 0);
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", String)
    ], FunChartComponent.prototype, "y1AxisLabel", void 0);
    FunChartComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'fun-chart',
            template: __webpack_require__(/*! ./fun-chart.component.html */ "./src/app/fun-chart/fun-chart.component.html"),
            styles: [__webpack_require__(/*! ./fun-chart.component.css */ "./src/app/fun-chart/fun-chart.component.css")]
        }),
        __metadata("design:paramtypes", [])
    ], FunChartComponent);
    return FunChartComponent;
}());

//
//                 if (ctrl.charting) {
//                     $timeout(function () {
//                          if (ctrl.chartType === "line-chart") {
//                             let series = angular.copy(ctrl.values);
//                             let chartInfo = {
//                                 chart: {
//                                     height: ctrl.height,
//                                     width: ctrl.width
//                                 },
//                                 title: {
//                                     text: ctrl.title
//                                 },
//
//                                 subtitle: {
//                                     text: ''
//                                 },
//                                 xAxis: {
//                                     categories: ctrl.series,
//                                     title: {
//                                         text: ctrl.xaxisTitle
//                                     }
//                                 },
//
//                                 yAxis: {
//                                     title: {
//                                         text: ctrl.yaxisTitle
//                                     }
//                                 },
//                                 legend: {
//                                     layout: 'vertical',
//                                     align: 'right',
//                                     verticalAlign: 'middle'
//                                 },
//                                 credits: {
//                                     enabled: false
//                                 },
//                                 plotOptions: {
//                                     line: {
//                                         animation: false,
//                                         marker: {
//                                             enabled: true
//                                         }
//                                     },
//                                     series: {
//                                         animation: false,
//                                         label: {
//                                             connectorAllowed: false
//                                         },
//                                         point: {
//                                             events: {
//                                                 click: function (e) {
//                                                     /*location.href = 'https://en.wikipedia.org/wiki/' +
//                                                         this.options.key;*/
//                                                     console.log(ctrl.pointClickCallback);
//                                                     ctrl.pointClickCallback()(e.point);
//                                                 }
//                                             }
//                                         }
//                                     }
//
//                                 },
//
//                                 series: series,
//
//
//                                 responsive: {
//                                     rules: [{
//                                         condition: {
//                                             maxWidth: 500
//                                         },
//                                         chartOptions: {
//                                             legend: {
//                                                 layout: 'horizontal',
//                                                 align: 'center',
//                                                 verticalAlign: 'bottom'
//                                             }
//                                         }
//                                     }]
//                                 }
//
//                             };
//                             try {
//                                 if (ctrl.xaxisFormatter && ctrl.xaxisFormatter()()) {
//                                     chartInfo.xAxis["labels"] = {formatter: function () {
//                                         return ctrl.xaxisFormatter()(this.value);
//                                     }};
//                                 }
//
//                                 if (ctrl.tooltipFormatter && ctrl.tooltipFormatter()()) {
//                                     chartInfo.tooltip = {
//                                         formatter: function () {
//                                             return ctrl.tooltipFormatter()(this.x, this.y);
//                                         }
//                                     }
//                                 }
//
//                                 if (ctrl.pointClickCallback && ctrl.pointClickCallback()()) {
//                                     chartInfo.plotOptions.series["point"] = {
//                                         events: {
//                                             click: function (e) {
//                                                 ctrl.pointClickCallback()(e.point);
//                                             }
//                                         }
//                                     }
//                                 }
//                             } catch (e) {
//                                 console.log(e);
//
//                             }
//
//
//                             Highcharts.chart("c-" + $scope.genId, chartInfo);
//                         } }, 10);
//
//                 }
//             }, true);
//
//         ctrl.$onInit = function () {
//
//             //["Sent", "Received"];
//             $scope.xValue = 0;
//             $scope.values = {};
//             angular.forEach(ctrl.series, function (input) {
//                 $scope.values[input] = [];
//             });
//
//             /*$timeout($scope.repeat, 1000);*/
//
//
//         };
//
//         $scope.repeat = function () {
//             console.log(ctrl);
//             $timeout($scope.repeat, 1000);
//         }
//
//     }
//             autoUpdate: '<',
//             charting: '<',
//             values: '<',
//             updateChartsNow: '=',
//             showLegend: '<',
//             series: '<',
//             title: '<',
//             minimal: '<',
//             chartType: '@',
//             colors: '<',
//             width: '<',
//             height: '<',
//             xaxisTitle: '<',
//             yaxisTitle: '<',
//             pointClickCallback: '&',
//             xaxisFormatter: '&',
//             tooltipFormatter: '&'
//         }
//     });
//
// })(window.angular);


/***/ }),

/***/ "./src/app/fun-metric-chart/fun-metric-chart.component.css":
/*!*****************************************************************!*\
  !*** ./src/app/fun-metric-chart/fun-metric-chart.component.css ***!
  \*****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "a {\n  cursor: pointer;\n}\n"

/***/ }),

/***/ "./src/app/fun-metric-chart/fun-metric-chart.component.html":
/*!******************************************************************!*\
  !*** ./src/app/fun-metric-chart/fun-metric-chart.component.html ***!
  \******************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<link rel=\"stylesheet\" type=\"text/css\" href=\"https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css\" />\n<div>\n        <div [ngSwitch]=\"timeMode\">\n            <div *ngSwitchCase=\"'all'\">\n                <a (click)=\"setTimeMode('week')\"> Week </a>/\n                <a (click)=\"setTimeMode('month')\"> Month </a>/\n                <b><u><a (click)=\"setTimeMode('all')\"> All </a></u></b>\n            </div>\n            <div *ngSwitchCase=\"'week'\">\n                <b><u><a (click)=\"setTimeMode('week')\"> Week </a></u></b>/\n                <a (click)=\"setTimeMode('month')\"> Month </a>/\n                <a (click)=\"setTimeMode('all')\"> All </a>\n            </div>\n            <div *ngSwitchCase=\"'month'\">\n                <a (click)=\"setTimeMode('week')\"> Week </a>/\n                <b><u><a (click)=\"setTimeMode('month')\"> Month </a></u></b>/\n                <a (click)=\"setTimeMode('all')\"> All </a>\n            </div>\n        </div>\n        <!--<fun-chart values=\"values\" series=\"series\" title=\"$ctrl.chartName\" charting=\"charting\" chart-type=\"line-chart\"-->\n               <!--width=\"width\" height=\"height\" xaxis-title=\"chart1XaxisTitle\" yaxis-title=\"chart1YaxisTitle\"-->\n               <!--point-click-callback=\"pointClickCallback\" xaxis-formatter=\"xAxisFormatter\"-->\n               <!--tooltip-formatter=\"tooltipFormatter\">-->\n        <!--</fun-chart>-->\n      <!--<fun-chart [yValues]=\"yValues\" [xValues]=\"xValues\" [title]=\"title\" [xAxisLabel]=\"xAxisLabel\" [yAxisLabel]=\"yAxisLabel\"></fun-chart>-->\n  <!--<div *ngFor=\"let in of counter(50)\">-->\n  <fun-chart [y1Values]=\"values\" [xValues]=\"series\" [title]=\"chartName\" [xAxisLabel]=\"xAxisLabel\" [y1AxisLabel]=\"yAxisLabel\"></fun-chart>\n  <!--</div>-->\n    <br>\n\n     <b>Description:   </b><a *ngIf=\"!editingDescription\" (click)=\"toggleEdit()\"><i class=\"fa fa-pencil\"></i></a>\n    <br>\n    <div [innerHTML]=\"inner.currentDescription\"></div>\n    <div *ngIf=\"editingDescription\">\n        <br>\n        <textarea rows=\"4\" [(ngModel)]=\"inner.currentDescription\" style=\"min-width: 100%;\"></textarea>\n        <button class=\"btn btn-success\" (click)=\"submit()\">Submit</button>\n        <a style=\"padding: 5px;\" (click)=\"toggleEdit()\">Cancel</a>\n    </div>\n</div>\n<div *ngIf=\"modelName !== 'MetricContainer'\" style=\"padding-top: 10px; padding-bottom: 10px;\">\n    <div>\n    <button [attr.id]=\"'show_tables_' + metricId\" type=\"button\" class=\"btn arrow_btn btn-lg btn-info collapsed\" data-toggle=\"collapse\" [attr.data-target]=\"'#showing_tables_' + metricId\"\n            style=\"text-align: left; font-size: 14px; padding: 5px; padding-left: 0; border-color: black; border: 0 solid; background: white; color: black; outline: none;\">Show Tables</button>\n  <div [attr.id]=\"'showing_tables_' + metricId\" class=\"collapse\">\n      <div *ngIf=\"headers\">\n          <!--<fun-table (nextPage)=\"setValues($event)\" [data]=\"data\">-->\n          <!--</fun-table>-->\n      </div>\n      <div>\n          <a href=\"{{ '#show_tables_' + metricId }}\" style=\"float:right\" (click)=\"changeClass('#showing_tables_' + metricId, '#show_tables_' + metricId)\">Hide Tables</a>\n      </div>\n      <br>\n      <br>\n      <div class=\"closed-section\"></div>\n\n      <!--<button type=\"button\" class=\"btn btn1 btn-lg btn-info collapsed\" data-toggle=\"collapse\" data-target=\"#demo\" style=\"text-align: left; font-size: 14px; padding: 5px; border-color: black; border: 0px solid; width: 100%; background: white; color: black;\">Hide Tables</button>-->\n  </div>\n    </div>\n    <div>\n    <button [attr.id]=\"'configure_' + metricId\" type=\"button\" ng-class=\"after\" class=\"btn arrow_btn btn-lg btn-info collapsed\" data-toggle=\"collapse\" [attr.data-target]=\"'#show_configure_' + metricId\"\n            style=\"text-align: left; font-size: 14px; padding: 5px; padding-left: 0; border-color: black; border: 0 solid; background: white; color: black; outline: none;\">Configure</button>\n  <div [attr.id]=\"'show_configure_' + metricId\" class=\"collapse\">\n       <div class=\"row\">\n           <!--<div class=\"col-lg-10 col-xl-10 pull-left\">-->\n               <!--<table class=\"table table-nonfluid table-borderless\"-->\n                      <!--ng-repeat=\"dataSet in previewDataSets track by $index\">-->\n                   <!--<tr>-->\n                       <!--<th>Name</th>-->\n                       <!--<th>Field</th>-->\n                       <!--<th>Min</th>-->\n                       <!--<th>Max</th>-->\n                       <!--<th>Expected</th>-->\n                   <!--</tr>-->\n                   <!--<tr>-->\n                       <!--<td>-->\n                           <!--{{ dataSet.name }}-->\n                       <!--</td>-->\n                       <!--<td>-->\n                           <!--{{ dataSet.output.name }}-->\n                       <!--</td>-->\n                       <!--<td>-->\n                           <!--<input type=\"number\" ng-model=\"dataSet.output.min\" ng-value=\"dataSet.output.min\"-->\n                                  <!--style=\"width: 100px\">-->\n                       <!--</td>-->\n                       <!--<td><input type=\"number\" ng-model=\"dataSet.output.max\" ng-value=\"dataSet.output.max\"-->\n                                  <!--style=\"width: 100px\"></td>-->\n                       <!--<td><input type=\"number\" ng-model=\"dataSet.output.expected\"-->\n                                  <!--ng-value=\"dataSet.output.expected\"-->\n                                  <!--style=\"width: 100px\"></td>-->\n                   <!--</tr>-->\n               <!--</table>-->\n               <!--<p><input type=\"checkbox\" ng-checked=\"negativeGradient\" ng-model=\"inner.negativeGradient\">&nbsp;Negative gradient</p>-->\n               <!--<p><input type=\"checkbox\" ng-checked=\"leaf\" ng-model=\"inner.leaf\">&nbsp;Leaf</p>-->\n           <!--</div>-->\n       </div>\n      <div class=\"row\">\n          <div style=\"padding: 10px;\">\n              <button class=\"btn btn-success\" (click)=\"submit()\">Submit</button>\n              <a href=\"{{ '#configure_' + metricId }}\" (click)=\"changeClass('#show_configure_' + metricId, '#configure_' + metricId)\">Cancel</a>\n          </div>\n      </div>\n  </div>\n    </div>\n\n    </div>\n"

/***/ }),

/***/ "./src/app/fun-metric-chart/fun-metric-chart.component.ts":
/*!****************************************************************!*\
  !*** ./src/app/fun-metric-chart/fun-metric-chart.component.ts ***!
  \****************************************************************/
/*! exports provided: FunMetricChartComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "FunMetricChartComponent", function() { return FunMetricChartComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _services_api_api_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../services/api/api.service */ "./src/app/services/api/api.service.ts");
/* harmony import */ var _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../services/logger/logger.service */ "./src/app/services/logger/logger.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var FunMetricChartComponent = /** @class */ (function () {
    function FunMetricChartComponent(apiService, loggerService) {
        this.apiService = apiService;
        this.loggerService = loggerService;
        this.editingDescription = false;
        this.inner = {};
        this.atomic = false;
        this.previewDataSets = null;
        this.waitTime = 0;
        this.pointClickCallback = null;
        this.yValues = [];
        this.xValues = [];
    }
    FunMetricChartComponent.prototype.ngOnInit = function () {
        var _this = this;
        this.yValues.push({ name: 'series 1', data: [1, 2, 3, 4, 5] });
        this.yValues.push({ name: 'series 2', data: [6, 7, 8, 9, 10] });
        this.yValues.push({ name: 'series 3', data: [11, 12, 13, 14, 15] });
        this.yValues.push({ name: 'series 4', data: [16, 17, 18, 19, 20] });
        this.yValues.push({ name: 'series 5', data: [21, 22, 23, 24, 25] });
        this.xValues.push([0, 1, 2, 3, 4]);
        this.chartTitle = "Funchart";
        this.xAxisLabel = "Date";
        this.yAxisLabel = "Range";
        this.status = "idle";
        this.showingTable = false;
        this.setDefault();
        this.headers = null;
        this.metricId = -1;
        this.editingDescription = false;
        this.inner = {};
        this.inner.currentDescription = "TBD";
        this.currentDescription = "---";
        if (this.chartName) {
            this.fetchInfo();
        }
        this.values = null;
        this.charting = true;
        this.xAxisFormatter = null;
        this.tooltipFormatter = null;
        this.buildInfo = null;
        this.fetchBuildInfo();
        // if (this.pointClickCallback) {
        //   this.pointClickCallback = (point) => {
        //     if (!$attrs.pointClickCallback) return null;
        //     this.pointClickCallback()(point);
        //   };
        // }
        this.xAxisFormatter = function (value) {
            var s = "Error";
            var monthNames = ["null", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            var r = /(\d{4})-(\d{2})-(\d{2})/g;
            var match = r.exec(value);
            if (_this.timeMode === "month") {
                if (match) {
                    var month = parseInt(match[2]);
                    s = monthNames[month];
                }
            }
            else {
                if (match) {
                    s = match[2] + "/" + match[3];
                }
            }
            return s;
        };
        this.tooltipFormatter = function (x, y) {
            var softwareDate = "Unknown";
            var hardwareVersion = "Unknown";
            var sdkBranch = "Unknown";
            var gitCommit = "Unknown";
            var r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
            var match = r.exec(x);
            var key = "";
            if (match) {
                key = match[1];
            }
            else {
                var reg = /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})/g;
                match = reg.exec(x);
                if (match) {
                    key = match[1].replace('T', ' ');
                }
            }
            var s = "Error";
            if (_this.buildInfo && key in _this.buildInfo) {
                softwareDate = _this.buildInfo[key]["software_date"];
                hardwareVersion = _this.buildInfo[key]["hardware_version"];
                sdkBranch = _this.buildInfo[key]["fun_sdk_branch"];
                s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
                s += "<b>Software date:</b> " + softwareDate + "<br>";
                s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
                s += "<b>Git commit:</b> " + _this.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "") + "<br>";
                s += "<b>Value:</b> " + y + "<br>";
            }
            else {
                s = "<b>Value:</b> " + y + "<br>";
            }
            return s;
        };
    };
    FunMetricChartComponent.prototype.ngOnChanges = function () {
        this.setDefault();
        this.fetchInfo();
    };
    FunMetricChartComponent.prototype.fetchInfo = function () {
        var _this = this;
        var payload = {};
        payload["metric_model_name"] = this.modelName;
        payload["chart_name"] = this.chartName;
        if (!this.chartInfo) {
            this.apiService.post("/metrics/chart_info", payload).subscribe(function (chartInfo) {
                _this.chartInfo = chartInfo;
                if (_this.chartInfo !== null) {
                    _this.previewDataSets = _this.chartInfo.data.data_sets;
                    _this.currentDescription = _this.chartInfo.data.description;
                    _this.inner.currentDescription = _this.currentDescription;
                    _this.negativeGradient = !_this.chartInfo.data.positive;
                    _this.inner.negativeGradient = _this.negativeGradient;
                    _this.leaf = _this.chartInfo.data.leaf;
                    _this.inner.leaf = _this.leaf;
                    _this.status = "idle";
                }
                // let thisChartInfo = chartInfo;
                setTimeout(function () {
                    _this.fetchMetricsData(_this.modelName, _this.chartName, _this.chartInfo, null);
                }, _this.waitTime);
            }, function (error) {
                _this.loggerService.error("fun_metric_chart: chart_info");
            });
        }
        else {
            setTimeout(function () {
                _this.fetchMetricsData(_this.modelName, _this.chartName, _this.chartInfo, null);
            }, this.waitTime);
        }
    };
    FunMetricChartComponent.prototype.setDefault = function () {
        this.timeMode = "all";
    };
    FunMetricChartComponent.prototype.toggleEdit = function () {
        this.editingDescription = !this.editingDescription;
    };
    FunMetricChartComponent.prototype.changeClass = function (divId, buttonId) {
        var divIdClass = window.document.querySelector(divId);
        divIdClass.removeClass('in');
        var collapseArrow = window.document.querySelector(buttonId);
        collapseArrow.addClass('collapsed');
    };
    FunMetricChartComponent.prototype.cleanValue = function (key, value) {
        try {
            if (key === "input_date_time") {
                var s = "Error";
                var r = /(\d{4})-(\d{2})-(\d{2})/g;
                var match = r.exec(value);
                if (match) {
                    s = match[2] + "/" + match[3];
                }
                return s;
            }
            else {
                return value;
            }
        }
        catch (e) {
        }
    };
    FunMetricChartComponent.prototype.submit = function () {
        var _this = this;
        //this.previewDataSets = this.copyChartInfo.data_sets;
        var payload = {};
        payload["metric_model_name"] = this.modelName;
        payload["chart_name"] = this.chartName;
        payload["data_sets"] = this.previewDataSets;
        payload["description"] = this.inner.currentDescription;
        payload["negative_gradient"] = this.inner.negativeGradient;
        payload["leaf"] = this.inner.leaf;
        this.apiService.post('/metrics/update_chart', payload).subscribe(function (data) {
            if (data) {
                alert("Submitted");
            }
            else {
                alert("Submission failed. Please check alerts");
            }
        }, function (error) {
            _this.loggerService.error("EditChart: Submit");
        });
        this.editingDescription = false;
    };
    FunMetricChartComponent.prototype.fetchChartInfo = function () {
        var _this = this;
        var payload = {};
        payload["metric_model_name"] = this.modelName;
        payload["chart_name"] = this.chartName;
        if (!this.chartInfo) {
            return this.apiService.post("/metrics/chart_info", payload).subscribe(function (chartInfo) {
                _this.chartInfo = chartInfo;
                if (_this.chartInfo !== null) {
                    _this.previewDataSets = _this.chartInfo.data_sets;
                    _this.currentDescription = _this.chartInfo.description;
                    _this.inner.currentDescription = _this.currentDescription;
                    _this.negativeGradient = !_this.chartInfo.positive;
                    _this.inner.negativeGradient = _this.negativeGradient;
                    _this.leaf = _this.chartInfo.leaf;
                    _this.inner.leaf = _this.leaf;
                    _this.status = "idle";
                }
                return _this.chartInfo;
            }, function (error) {
                _this.loggerService.error("fun_metric_chart: chart_info");
            });
        }
        else {
            return this.chartInfo;
        }
    };
    FunMetricChartComponent.prototype.fetchBuildInfo = function () {
        var _this = this;
        this.apiService.get('/regression/jenkins_job_id_maps').subscribe(function (data) {
            _this.apiService.get('/regression/build_to_date_map').subscribe(function (data) {
                _this.buildInfo = data;
            }, function (error) {
                _this.loggerService.error("regression/build_to_date_map");
            });
        }, function (error) {
            _this.loggerService.error("fetchBuildInfo");
        });
    };
    FunMetricChartComponent.prototype.showTables = function () {
        this.showingTable = !this.showingTable;
    };
    FunMetricChartComponent.prototype.setTimeMode = function (mode) {
        this.timeMode = mode;
        if (this.chartInfo) {
            this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, this.previewDataSets); // TODO: Race condition on chartInfo
        }
        else {
            this.fetchMetricsData(this.modelName, this.chartName, null, this.previewDataSets); // TODO: Race condition on chartInfo
        }
    };
    FunMetricChartComponent.prototype.describeTable = function (metricModelName) {
        var _this = this;
        var self = this;
        if (!this.tableInfo && metricModelName !== 'MetricContainer') {
            return this.apiService.get("/metrics/describe_table/" + metricModelName).subscribe(function (tableInfo) {
                //console.log("FunMetric: Describe table: " + metricModelName);
                self.tableInfo = tableInfo;
                return self.tableInfo;
            }, function (error) {
                _this.loggerService.error("fetchMetricsData");
            });
        }
        else {
            return this.tableInfo;
        }
    };
    FunMetricChartComponent.prototype.getDatesByTimeMode = function (dateList) {
        var len = dateList.length;
        var filteredDate = [];
        var result = [[len, 0]];
        if (this.timeMode === "week") {
            for (var i = len - 1; i >= 0; i = i - 7) {
                if (i >= 7) {
                    filteredDate.push([i, i - 7 + 1]);
                }
                else {
                    filteredDate.push([i, 0]);
                }
            }
            result = filteredDate.reverse();
        }
        else if (this.timeMode === "month") {
            var i = len - 1;
            var startIndex = len - 1;
            var latestDate = new Date(dateList[i].replace(/\s+/g, 'T'));
            var latestMonth = latestDate.getUTCMonth();
            while (i >= 0) {
                var currentDate = new Date(dateList[i].replace(/\s+/g, 'T'));
                var currentMonth = currentDate.getUTCMonth();
                if (currentMonth !== latestMonth) {
                    filteredDate.push([startIndex, i + 1]);
                    latestMonth = currentMonth;
                    startIndex = i;
                }
                if (i === 0) {
                    filteredDate.push([startIndex, i]);
                }
                i--;
            }
            result = filteredDate.reverse();
        }
        else {
            for (var i = len - 1; i >= 0; i--) {
                filteredDate.push([i, i]);
            }
            result = filteredDate.reverse();
        }
        return result;
    };
    FunMetricChartComponent.prototype.shortenKeyList = function (keyList) {
        var newList = [];
        for (var _i = 0, keyList_1 = keyList; _i < keyList_1.length; _i++) {
            var key = keyList_1[_i];
            var r = /(\d{4})-(\d{2})-(\d{2})/g;
            var match = r.exec(key);
            var s = match[2] + "/" + match[3];
            newList.push(s);
        }
        return newList;
    };
    FunMetricChartComponent.prototype.fixMissingDates = function (dates) {
        var firstString = dates[0].replace(/\s+/g, 'T');
        //firstString = firstString.replace('+', 'Z');
        //firstString = firstString.substring(0, firstString.indexOf('Z'));
        var firstDate = new Date(firstString);
        var today = new Date();
        var yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        yesterday.setHours(23, 59, 59);
        var lastDate = yesterday;
        var currentDate = firstDate;
        var datesIndex = 0;
        var finalDates = [];
        while (currentDate <= yesterday) {
            //console.log(currentDate);
            if ((datesIndex < dates.length) && this.sameDay(new Date(dates[datesIndex].replace(/\s+/g, 'T')), currentDate)) {
                finalDates.push(dates[datesIndex]);
                datesIndex++;
                while ((datesIndex < dates.length) && this.sameDay(new Date(dates[datesIndex].replace(/\s+/g, 'T')), currentDate)) {
                    //finalDates.push(dates[datesIndex]);
                    datesIndex++;
                }
            }
            else {
                //currentDate.setHours(currentDate.getHours() - currentDate.getTimezoneOffset() / 60);
                var tempDate = currentDate;
                tempDate.setHours(0);
                tempDate.setMinutes(0);
                tempDate.setSeconds(1);
                tempDate = new Date(tempDate.getTime() - (tempDate.getTimezoneOffset() * 60000));
                finalDates.push(tempDate.toISOString().replace('T', ' ')); //TODO: convert zone correctly
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }
        var j = 0;
        return finalDates;
    };
    FunMetricChartComponent.prototype.sameDay = function (d1, d2) {
        return d1.getFullYear() === d2.getFullYear() &&
            d1.getMonth() === d2.getMonth() &&
            d1.getDate() === d2.getDate();
    };
    FunMetricChartComponent.prototype.fetchData = function (metricModelName, chartName, chartInfo, previewDataSets, tableInfo) {
        var _this = this;
        var payload = {};
        payload["metric_model_name"] = metricModelName;
        payload["chart_name"] = chartName;
        payload["preview_data_sets"] = previewDataSets;
        payload["metric_id"] = -1;
        if (chartInfo) {
            payload["metric_id"] = chartInfo.data["metric_id"];
            this.metricId = chartInfo.data["metric_id"];
        }
        if (metricModelName !== 'MetricContainer') {
            this.status = "idle";
            this.tableInfo = tableInfo;
            var filterDataSets = [];
            if (previewDataSets) {
                filterDataSets = previewDataSets;
            }
            else {
                //console.log("Chart Info:" + chartInfo);
                if (chartInfo) {
                    filterDataSets = chartInfo.data['data_sets'];
                    //console.log("C DS:" + chartInfo.data_sets);
                }
            }
            this.filterDataSets = filterDataSets;
            this.status = "Fetch data";
            this.apiService.post("/metrics/data", payload).subscribe(function (allDataSets) {
                self.status = "idle";
                if (allDataSets.length === 0) {
                    _this.values = null;
                    return;
                }
                var keySet = new Set();
                /*
                let firstDataSet = allDataSets[0];
                firstDataSet.forEach((oneRecord) => {
                    keySet.add(oneRecord.input_date_time.toString());
                });*/
                for (var _i = 0, _a = allDataSets.data; _i < _a.length; _i++) {
                    var oneDataSet = _a[_i];
                    for (var _b = 0, oneDataSet_1 = oneDataSet; _b < oneDataSet_1.length; _b++) {
                        var oneRecord = oneDataSet_1[_b];
                        keySet.add(oneRecord.input_date_time.toString());
                    }
                }
                // allDataSets.foreach((oneDataSet) => {
                //   oneDataSet.foreach((oneRecord) => {
                //     keySet.add(oneRecord.input_date_time.toString());
                //   });
                // });
                var keyList = Array.from(keySet);
                keyList.sort();
                _this.shortenKeyList(keyList);
                keyList = _this.fixMissingDates(keyList);
                var originalKeyList = keyList;
                keyList = _this.getDatesByTimeMode(keyList);
                var chartDataSets = [];
                var seriesDates = [];
                var dataSetIndex = 0;
                _this.allData = allDataSets;
                _this.status = "Preparing chart data-sets";
                for (var _c = 0, _d = allDataSets.data; _c < _d.length; _c++) {
                    var oneDataSet = _d[_c];
                    var oneChartDataArray = [];
                    for (var i = 0; i < keyList.length; i++) {
                        var output = null;
                        var total = 0;
                        var count = 0;
                        var matchingDateFound = false;
                        seriesDates.push(originalKeyList[keyList[i][0]]);
                        var startIndex = keyList[i][0];
                        var endIndex = keyList[i][1];
                        while (startIndex >= endIndex) {
                            for (var j = 0; j < oneDataSet.length; j++) {
                                var oneRecord = oneDataSet[j];
                                if (oneRecord.input_date_time.toString() === originalKeyList[startIndex]) {
                                    matchingDateFound = true;
                                    var outputName = _this.filterDataSets[dataSetIndex].output.name;
                                    output = oneRecord[outputName];
                                    total += output;
                                    count++;
                                    if (chartInfo && chartInfo.y1_axis_title) {
                                        _this.chart1YaxisTitle = chartInfo.data.y1_axis_title;
                                    }
                                    else {
                                        _this.chart1YaxisTitle = tableInfo.data[outputName].verbose_name;
                                    }
                                    if (_this.y1AxisTitle) {
                                        _this.chart1YaxisTitle = _this.y1AxisTitle;
                                    }
                                    _this.chart1XaxisTitle = tableInfo.data["input_date_time"].verbose_name;
                                }
                            }
                            startIndex--;
                        }
                        if (count !== 0) {
                            output = total / count;
                        }
                        var thisMinimum = _this.filterDataSets[dataSetIndex].output.min;
                        var thisMaximum = _this.filterDataSets[dataSetIndex].output.max;
                        oneChartDataArray.push(_this.getValidatedData(output, thisMinimum, thisMaximum));
                    }
                    var oneChartDataSet = { name: _this.filterDataSets[dataSetIndex].name, data: oneChartDataArray };
                    chartDataSets.push(oneChartDataSet);
                    dataSetIndex++;
                }
                _this.status = "idle";
                _this.series = seriesDates;
                _this.values = chartDataSets;
                _this.headers = _this.tableInfo;
            }, function (error) {
                _this.loggerService.error("fetchMetricsData");
            });
        }
        else {
            this.status = "Fetch data";
            console.log("Fetch Scores");
            this.apiService.post('/metrics/scores', payload).subscribe(function (data) {
                self.status = "idle";
                if (data.length === 0) {
                    _this.values = null;
                    return;
                }
                var values = [];
                var series = [];
                var keyList = Object.keys(data.scores);
                keyList.sort();
                for (var _i = 0, keyList_2 = keyList; _i < keyList_2.length; _i++) {
                    var dateTime = keyList_2[_i];
                    //values.push(data.scores[dateTime].score);
                    var d = new Date(1000 * Number(dateTime)).toISOString();
                    //let dateSeries = d.setUTCSeconds(dateTime);
                    series.push(d);
                }
                _this.shortenKeyList(series);
                if (series.length === 0) {
                    _this.series = null;
                    _this.values = null;
                }
                else {
                    series = _this.fixMissingDates(series);
                    var dateSeries = [];
                    var seriesRange = _this.getDatesByTimeMode(series);
                    for (var i = 0; i < seriesRange.length; i++) {
                        var startIndex = seriesRange[i][0];
                        var endIndex = seriesRange[i][1];
                        var count = 0;
                        var total = 0;
                        dateSeries.push(series[startIndex]);
                        while (startIndex >= endIndex) {
                            for (var j = 0; j < keyList.length; j++) {
                                var dateTime = keyList[j];
                                var d = new Date(dateTime * 1000).toISOString();
                                if (d === series[startIndex]) {
                                    total += data.scores[dateTime].score;
                                    count++;
                                }
                            }
                            startIndex--;
                        }
                        if (count !== 0) {
                            var average = total / count;
                            values.push(average);
                        }
                        else {
                            values.push(null);
                        }
                    }
                    _this.values = [{ data: values }];
                    _this.series = dateSeries;
                    _this.status = "idle";
                    //let keyList = Array.from(keySet);
                }
            });
        }
    };
    FunMetricChartComponent.prototype.fetchMetricsData = function (metricModelName, chartName, chartInfo, previewDataSets) {
        var _this = this;
        this.title = chartName;
        var self = this;
        if (!chartName) {
            return;
        }
        var self = this;
        if (!this.tableInfo && metricModelName !== 'MetricContainer') {
            return this.apiService.get("/metrics/describe_table/" + metricModelName).subscribe(function (tableInfo) {
                //console.log("FunMetric: Describe table: " + metricModelName);
                self.tableInfo = tableInfo;
                // return self.tableInfo;
                self.fetchData(metricModelName, chartName, chartInfo, previewDataSets, tableInfo);
            }, function (error) {
                _this.loggerService.error("fetchMetricsData");
            });
        }
        else {
            // return this.tableInfo;
            this.fetchData(metricModelName, chartName, chartInfo, previewDataSets, this.tableInfo);
        }
    };
    FunMetricChartComponent.prototype.getValidatedData = function (data, minimum, maximum) {
        var result = data;
        if (data < 0) {
            data = null;
        }
        result = {
            y: data,
            marker: {
                radius: 3
            }
        };
        return result;
    };
    FunMetricChartComponent.prototype.counter = function (num) {
        var newArray = new Array(num);
        return newArray;
    };
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", Object)
    ], FunMetricChartComponent.prototype, "chartName", void 0);
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", Object)
    ], FunMetricChartComponent.prototype, "modelName", void 0);
    FunMetricChartComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'fun-metric-chart',
            template: __webpack_require__(/*! ./fun-metric-chart.component.html */ "./src/app/fun-metric-chart/fun-metric-chart.component.html"),
            styles: [__webpack_require__(/*! ./fun-metric-chart.component.css */ "./src/app/fun-metric-chart/fun-metric-chart.component.css")]
        }),
        __metadata("design:paramtypes", [_services_api_api_service__WEBPACK_IMPORTED_MODULE_1__["ApiService"], _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_2__["LoggerService"]])
    ], FunMetricChartComponent);
    return FunMetricChartComponent;
}());



/***/ }),

/***/ "./src/app/fun-table/fun-table.component.css":
/*!***************************************************!*\
  !*** ./src/app/fun-table/fun-table.component.css ***!
  \***************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".tableContainer {\n  margin: 5px;\n  padding: 5px;\n}\n/*.switch {*/\n/*position: relative;*/\n/*display: inline-block;*/\n/*width: 40px;*/\n/*height: 20px;*/\n/*}*/\n/*.switch input {display:none;}*/\n/*.slider {*/\n/*position: absolute;*/\n/*cursor: pointer;*/\n/*top: 0;*/\n/*left: 0;*/\n/*right: 0;*/\n/*bottom: 0;*/\n/*background-color: #ccc;*/\n/*-webkit-transition: .4s;*/\n/*transition: .4s;*/\n/*}*/\n/*.slider:before {*/\n/*position: absolute;*/\n/*content: \"\";*/\n/*height: 20px;*/\n/*width: 20px;*/\n/*background-color: white;*/\n/*-webkit-transition: .4s;*/\n/*transition: .4s;*/\n/*}*/\n/*input:checked + .slider {*/\n/*background-color: #2196F3;*/\n/*}*/\n/*input:focus + .slider {*/\n/*box-shadow: 0 0 1px #2196F3;*/\n/*}*/\n/*input:checked + .slider:before {*/\n/*-webkit-transform: translateX(26px);*/\n/*-ms-transform: translateX(26px);*/\n/*transform: translateX(26px);*/\n/*}*/\n/*!* Rounded sliders *!*/\n/*.slider.round {*/\n/*border-radius: 20px;*/\n/*}*/\n/*.slider.round:before {*/\n/*border-radius: 50%;*/\n/*}*/\n.fake-link {\n    color: blue;\n    text-decoration: underline;\n    cursor: pointer;\n}\na {\n  cursor: pointer;\n}\n#pageDiv {\n  float: right;\n  padding: 10px;\n}\n#advancedLink {\n  margin: 5px;\n}\n/*.switch {*/\n/*width: 40px;*/\n/*margin: 5px;*/\n/*}*/\n/*.slider {*/\n/*right: 10px;*/\n/*}*/\n/*.round {*/\n/*right: 5px;*/\n/*}*/\n/* The switch - the box around the slider */\n/*.switch {*/\n/*position: relative;*/\n/*display: inline-block;*/\n/*width: 30px;*/\n/*height: 15px;*/\n/*}*/\n/*!* Hide default HTML checkbox *!*/\n/*.switch input {display:none;}*/\n/*!* The slider *!*/\n/*.slider {*/\n/*position: absolute;*/\n/*cursor: pointer;*/\n/*top: 0;*/\n/*left: 0;*/\n/*right: 0;*/\n/*bottom: 0;*/\n/*background-color: #ccc;*/\n/*-webkit-transition: .4s;*/\n/*transition: .4s;*/\n/*}*/\n/*.slider:before {*/\n/*position: absolute;*/\n/*content: \"\";*/\n/*height: 10px;*/\n/*width: 10px;*/\n/*background-color: white;*/\n/*-webkit-transition: .4s;*/\n/*transition: .4s;*/\n/*}*/\n/*input.default:checked + .slider {*/\n/*background-color: #444;*/\n/*}*/\n/*input.primary:checked + .slider {*/\n/*background-color: #2196F3;*/\n/*}*/\n/*input.success:checked + .slider {*/\n/*background-color: #8bc34a;*/\n/*}*/\n/*input.info:checked + .slider {*/\n/*background-color: #3de0f5;*/\n/*}*/\n/*input.warning:checked + .slider {*/\n/*background-color: #FFC107;*/\n/*}*/\n/*input.danger:checked + .slider {*/\n/*background-color: #f44336;*/\n/*}*/\n/*input:focus + .slider {*/\n/*box-shadow: 0 0 1px #2196F3;*/\n/*}*/\n/*input:checked + .slider:before {*/\n/*-webkit-transform: translateX(26px);*/\n/*-ms-transform: translateX(26px);*/\n/*transform: translateX(26px);*/\n/*}*/\n/*!* Rounded sliders *!*/\n/*.slider.round {*/\n/*border-radius: 10px;*/\n/*}*/\n/*.slider.round:before {*/\n/*border-radius: 50%;*/\n/*}*/\n"

/***/ }),

/***/ "./src/app/fun-table/fun-table.component.html":
/*!****************************************************!*\
  !*** ./src/app/fun-table/fun-table.component.html ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<p>\n  table works!\n</p>\n<div class=\"card tableContainer\">\n  <div>\n    <div>\n      <!-- pager -->\n      <div id=\"pageDiv\" *ngIf=\"pager.pages && pager.pages.length\">\n        <span [ngClass]=\"{disabled:pager.currentPage === 1}\">\n          <a (click)=\"setPage(1)\">First </a>\n        </span>\n        <span [ngClass]=\"{disabled:pager.currentPage === 1}\">\n          <a (click)=\"setPage(pager.currentPage - 1)\">Previous </a>\n        </span>\n        <span *ngFor=\"let page of pager.pages\" [ngClass]=\"{active:pager.currentPage === page}\">\n          <a (click)=\"setPage(page)\">{{page}} </a>\n        </span>\n        <span [ngClass]=\"{disabled:pager.currentPage === pager.totalPages}\">\n          <a (click)=\"setPage(pager.currentPage + 1)\">Next </a>\n        </span>\n        <span [ngClass]=\"{disabled:pager.currentPage === pager.totalPages}\">\n          <a (click)=\"setPage(pager.totalPages)\">Last </a>\n        </span>\n      </div>\n      <!-- items being paged -->\n      <table class=\"table\" matSort (matSortChange)=\"sortData($event)\">\n        <tr>\n            <th *ngFor=\"let header of filtered(headers)\" mat-sort-header=\"{{headers.indexOf(header)}}\">{{ header }}</th>\n          <!--<th *ngFor=\"let header of headers\" mat-sort-header=\"{{headers.indexOf(header)}}\">{{ header }}</th>-->\n          <!-- th *ngFor=\"let key of headerIndexMap.keys()\" >{{ headers[key] }}</th-->\n        </tr>\n        <tr *ngFor=\"let item of pagedItems\">\n            <td *ngFor=\"let rowItems of filtered(item)\">{{rowItems}}</td>\n          <!--<td *ngFor=\"let rowItems of item\">{{rowItems}}</td>-->\n        </tr>\n      </table>\n      <a id=\"advancedLink\" (click)=\"editColumns()\">Advanced</a>\n    </div>\n  </div>\n\n  <div *ngIf=\"hideShowColumns\">\n    <div class=\"panel panel-default\">\n      <div class=\"panel-heading\">Columns</div>\n      <div class=\"panel-body\" style=\"vertical-align: center;\">\n          <table>\n            <tr *ngFor=\"let header of headers\">\n              <td>\n               <label>\n                 {{header}}\n               </label>\n              </td>\n              <td style=\"padding: 10px; margin: 5px;\">\n                <label class=\"switch\">\n          <input type=\"checkbox\" [checked]=\"headerIndexMap.get(headers.indexOf(header))\" (change)=\"setHeaders(header)\" class=\"switch\" data-toggle=\"toggle\" >\n          <span class=\"slider round\"></span>\n        </label>\n              </td>\n            </tr>\n          </table>\n\n      </div>\n    </div>\n    <button (click)=\"editColumns()\" style=\"margin: 5px;\">Close</button>\n  </div>\n</div>\n"

/***/ }),

/***/ "./src/app/fun-table/fun-table.component.ts":
/*!**************************************************!*\
  !*** ./src/app/fun-table/fun-table.component.ts ***!
  \**************************************************/
/*! exports provided: FunTableComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "FunTableComponent", function() { return FunTableComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _services_pager_pager_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../services/pager/pager.service */ "./src/app/services/pager/pager.service.ts");
/* harmony import */ var _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../services/logger/logger.service */ "./src/app/services/logger/logger.service.ts");
/* harmony import */ var _services_api_api_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../services/api/api.service */ "./src/app/services/api/api.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (undefined && undefined.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = y[op[0] & 2 ? "return" : op[0] ? "throw" : "next"]) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [0, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};




var FunTableComponent = /** @class */ (function () {
    function FunTableComponent(apiService, pagerService, logger, changeDetector) {
        this.apiService = apiService;
        this.pagerService = pagerService;
        this.logger = logger;
        this.changeDetector = changeDetector;
        this.hideShowColumns = false;
        this.headerIndexMap = new Map();
        // private allItems: any = [];
        this.pager = {};
        // originalData: any[];
        this.data = [];
        this.nextPage = new _angular_core__WEBPACK_IMPORTED_MODULE_0__["EventEmitter"]();
        this.logger.log("FunTableComponent init");
    }
    FunTableComponent_1 = FunTableComponent;
    FunTableComponent.prototype.ngOnInit = function () {
        if (this.data.rows && this.data.rows.length === 10000) {
            this.logger.log("10000 rows");
        }
        // this.doSomething1();
    };
    //setting the page number
    FunTableComponent.prototype.setPage = function (page) {
        // get pager object from service
        if (!this.data.all) {
            this.nextPage.emit(page);
        }
        else {
            this.setPagedItems(page);
        }
    };
    //setting the rows to be displayed by the template
    FunTableComponent.prototype.setPagedItems = function (page) {
        this.pager = this.pagerService.getPager(this.data.totalLength, page, this.pageSize);
        if (this.data.all) {
            this.pagedItems = this.rows.slice(this.pager.startIndex, this.pager.endIndex + 1);
        }
        else {
            this.pagedItems = this.rows.slice(0, this.pageSize);
        }
    };
    FunTableComponent.prototype.ngOnChanges = function () {
        if (this.data.currentPageIndex < 0) {
            this.logger.fatal("Page Index is less than 1");
        }
        else {
            this.rows = this.data.rows;
            this.headers = this.data.headers;
            // this.originalHeaders = this.data.headers;
            // this.originalRows = this.data.rows;
            for (var i in this.headers) {
                this.headerIndexMap.set(Number(i), true);
            }
            // this.headerIndexMap.set(0, true);
            // this.originalData = Array.from(this.rows);
            if (this.data.pageSize) {
                this.pageSize = this.data.pageSize;
            }
            else {
                this.pageSize = FunTableComponent_1.defaultPageSize;
            }
            this.setPagedItems(this.data.currentPageIndex);
            //this.setPage(1);
        }
    };
    //sorts the input rows in the data
    FunTableComponent.prototype.sortData = function (sort) {
        if (!sort.active || sort.direction === '') {
            // this.pagedItems = Array.from(this.originalData);
            // this.rows = this.pagedItems;
            // this.setPage(1);
            return;
        }
        this.pagedItems = this.rows.sort(function (a, b) {
            var isAscending = sort.direction === 'asc';
            if (sort.active) {
                return compare(a[sort.active], b[sort.active], isAscending);
            }
        });
        this.setPage(1);
    };
    //toggle between hide and show columns
    FunTableComponent.prototype.editColumns = function () {
        var _this = this;
        this.logger.log("Open form is entered");
        this.headerIndexMap.forEach(function (value, key) {
            console.log(Number(key), _this.headerIndexMap.get(Number(key)));
        });
        this.hideShowColumns = !this.hideShowColumns;
    };
    FunTableComponent.prototype.setHeaders = function (header) {
        // this.headerIndexMap.set(this.originalHeaders.indexOf(header), !this.headerIndexMap.get(this.originalHeaders.indexOf(header)));
        // let newHeaders = this.originalHeaders.filter(item => {
        //   if(this.headerIndexMap.get(this.originalHeaders.indexOf(item)) === true) {
        //     return true;
        //   }
        //   return false;
        // });
        // for (let i = 0; i < this.originalRows.length; i++) {
        //   this.rows[i] = this.originalRows[i].filter(item => {
        //   if(this.headerIndexMap.get(this.originalHeaders.indexOf(item)) === true) {
        //     return true;
        //   }
        //   return false;
        // });
        // }
        // this.headers = newHeaders;
        // // this.setPage(1);
        this.headerIndexMap.set(this.headers.indexOf(header), !this.headerIndexMap.get(this.headers.indexOf(header)));
        // this.filtered(this.headers);
        // this.changeDetector.detectChanges();
    };
    // filteredHeaders(indexMap) {
    //   console.log("filtered header");
    //   return this.headers.filter(item => {
    //           if(this.headers.indexOf(item) < indexMap.size && indexMap.get(this.headers.indexOf(item))) {
    //             return true;
    //           }
    //           return false;
    //       });
    // }
    FunTableComponent.prototype.filtered = function (item) {
        var _this = this;
        return item.filter(function (oldItem) {
            if (item.indexOf(oldItem) < _this.headerIndexMap.size && _this.headerIndexMap.get(item.indexOf(oldItem))) {
                return true;
            }
            return false;
        });
    };
    FunTableComponent.prototype.doSomething1 = function () {
        var _this = this;
        console.log("Doing Something1");
        var payload = { "metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"] };
        this.apiService.post('/metrics/scores', payload).subscribe(function (response) {
            //console.log(response.data);
        }, function (error) {
            //console.log(error);
            _this.delay(1000);
            _this.doSomething1();
        });
    };
    FunTableComponent.prototype.delay = function (ms) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(function () { return resolve(); }, ms); }).then(function () { return console.log("fired"); })];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    FunTableComponent.prototype.r = function () {
        return Math.random();
    };
    FunTableComponent.defaultPageSize = 10;
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", Object)
    ], FunTableComponent.prototype, "data", void 0);
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Output"])(),
        __metadata("design:type", _angular_core__WEBPACK_IMPORTED_MODULE_0__["EventEmitter"])
    ], FunTableComponent.prototype, "nextPage", void 0);
    FunTableComponent = FunTableComponent_1 = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'fun-table',
            template: __webpack_require__(/*! ./fun-table.component.html */ "./src/app/fun-table/fun-table.component.html"),
            styles: [__webpack_require__(/*! ./fun-table.component.css */ "./src/app/fun-table/fun-table.component.css")],
            changeDetection: _angular_core__WEBPACK_IMPORTED_MODULE_0__["ChangeDetectionStrategy"].Default
        }),
        __metadata("design:paramtypes", [_services_api_api_service__WEBPACK_IMPORTED_MODULE_3__["ApiService"], _services_pager_pager_service__WEBPACK_IMPORTED_MODULE_1__["PagerService"], _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_2__["LoggerService"], _angular_core__WEBPACK_IMPORTED_MODULE_0__["ChangeDetectorRef"]])
    ], FunTableComponent);
    return FunTableComponent;
    var FunTableComponent_1;
}());

function compare(a, b, isAsc) {
    return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
}


/***/ }),

/***/ "./src/app/performance/performance.component.css":
/*!*******************************************************!*\
  !*** ./src/app/performance/performance.component.css ***!
  \*******************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".info-box {\n  border: 1px;\n  border-color: #4CAF50;\n  border-style: solid;\n  border-radius: 5px;\n  width: inherit;\n  margin-top: 5px;\n}\n\n.info-box-header {\n  background-color: #dff0d8;\n  border-radius: 5px;\n\n}\n\n.info-box-text {\n  padding: 5px;\n}\n\n.aspect-label {\n  padding: 5px;\n}\n\n.aspect-label-text {\n  padding: 5px;\n}\n\n.fa-icon-green {\n  color: green;\n}\n\n.fa-icon-red {\n  color: red;\n}\n\n#score-table-parent {\n  display: table;\n  width: 60px;\n  height: 60px;\n  border: 3px solid lightsteelblue;\n  border-radius: 5px;\n}\n\n#score-table-child {\n  display: table-cell;\n  vertical-align: middle;\n  text-align: center;\n  font-size: 25px;\n  color: white;\n\n}\n\n#score-table-info-icon {\n  display: table-cell;\n  vertical-align: top;\n}\n\n.score-card {\n  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);\n  transition: 0.3s;\n  width: 40%;\n  background-color: #006699;\n}\n\n.fade-element-in.ng-enter {\n  opacity: 0;\n}\n\n.fade-element-in-init .fade-element-in.ng-enter {\n  opacity: 1;\n}\n\n.fade-element-in.ng-enter.ng-enter-active {\n  opacity: 1;\n}\n\n.fade-element-in.ng-leave {\n  transition: 0.3s linear all;\n  opacity: 1;\n}\n\n.fade-element-in.ng-leave.ng-leave-active {\n  opacity: 0;\n}\n\narrow-icon {\n  border: solid black;\n  border-width: 0 3px 3px 0;\n  display: inline-block;\n  padding: 3px;\n\n}\n\n.arrow-right {\n  transform: rotate(-45deg);\n  -webkit-transform: rotate(-45deg);\n\n}\n\n.arrow-down {\n  transform: rotate(45deg);\n  -webkit-transform: rotate(45deg);\n}\n\n.trend-button-green {\n  background-color: white;\n  border: 1px solid #4CAF50;\n  color: white;\n  text-align: center;\n  text-decoration: none;\n  border-radius: 1.5px;\n\n}\n\n.score-label {\n  -webkit-text-decoration: solid;\n          text-decoration: solid;\n}\n\n.trend-button-red {\n  background-color: white;\n  border: 1px solid red;\n  color: white;\n  text-align: center;\n  text-decoration: none;\n  border-radius: 1.5px;\n\n}\n"

/***/ }),

/***/ "./src/app/performance/performance.component.html":
/*!********************************************************!*\
  !*** ./src/app/performance/performance.component.html ***!
  \********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "\n<!--<fun-table (nextPage)=\"setValues($event)\" [data]=\"data\"></fun-table>-->\n<!--<li *ngFor='let in of counter(50) ;let i = index'>{{i}}-->\n  <!--<fun-chart></fun-chart>-->\n<!--</li>-->\n<div class=\"content\">\n  <div class=\"col-lg-6 col-xl-6 col-md-6\">\n    <div>\n      <table class=\"table table-nonfluid\">\n        <tr>\n          <th class=\"text-center\">Aspect</th>\n          <th class=\"text-center\">Score</th>\n          <th class=\"text-center\">#</th>\n          <!--th></th-->\n          <th class=\"text-center\">More Info</th>\n\n        </tr>\n        <tr class=\"fade-element-in\" ng-if=\"!node.hide\" ng-repeat=\"node in flatNodes track by $index\">\n          <td id=\"{{ node.guid }}\" class=\"child-transition\">\n                        <span ng-bind-html=\"getIndentHtml(node) | unsafe\">\n                        </span>\n            <a ng-if=\"node.leaf\" href=\"#\" ng-click=\"setCurrentChart(node)\">{{ node.label }}</a>\n            <a ng-if=\"!node.leaf\" href=\"#\" ng-click=\"showNonAtomicMetric(node)\">{{ node.label }}</a>\n            <!-- span ng-if=\"!node.leaf\">{{ node.label }}</span -->&nbsp\n            <span ng-if=\"node.numChildren\">\n                            <a href=\"#{{ node.guid }}\" ng-if=\"!node.collapsed\" ng-click=\"collapseNode(node)\">\n                                <span class=\"arrow-down\"></span>\n                            </a>\n                            <a href=\"#{{ node.guid }}\" ng-if=\"node.collapsed\" ng-click=\"expandNode(node)\">\n                                <span class=\"arrow-right\"></span>\n                            </a>\n                        </span>\n          </td>\n          <td class=\"text-center\">\n            <div ng-if=\"node.chartName !== 'All metrics'\" class=\"score-label\"><span style=\"vertical-align: top\"\n                                                                                    ng-bind-html=\"getTrendHtml(node) | unsafe\"></span>{{ node.goodness }}\n            </div>\n          </td>\n          <td class=\"text-center\">\n            <span ng-if=\"!node.leaf\">{{ node.numLeaves }}</span>\n          </td>\n\n          <td ng-bind-html=\"getStatusHtml(node) | unsafe\"></td>\n        </tr>\n      </table>\n\n    </div>\n    <!--<p>Last updated at: {{ lastStatusUpdateTime }}</p>-->\n  </div>\n\n\n  <div ng-if=\"mode\" class=\"card col-xl-6 col-lg-6 col-xxl-6\" ng-switch=\"mode\">\n    <div ng-switch-when=\"showingGoodnessTrend\">\n      <!-- fun-chart values=\"goodnessTrendValues\" show-legend=\"true\"\n                 title=\"goodnessTrendChartTitle\" charting=\"charting\" chart-type=\"line-chart\">\n      </fun-chart-->\n    </div>\n    <div ng-switch-when=\"showingAtomicMetric\">\n      <div ng-if=\"currentChartName\">\n        <table>\n          <tr>\n            <td>\n                                    <span id=\"score-table-parent\" class=\"score-card\">\n                                        <span id=\"score-table-child\">{{ currentNode.goodness }}\n                                        </span>\n                                    </span>\n            </td>\n            <td valign=\"top\" align=\"left\">\n                                <span id=\"score-table-info-icon\">\n                                    <i class=\"fa fa-info-circle\" style=\"padding: 2px\"\n                                       ng-click=\"showNodeInfoClick(currentNode)\">\n                                    </i>\n                                </span>\n            </td>\n            <td style=\"width: 100%\">\n                                <span style=\"float: right;\">\n                                            <button class=\"btn\" style=\"background-color: white\"\n                                                    ng-click=\"openAtomicTab()\">\n                                                <i class=\"fa fa-external-link\"></i></button>\n                                </span>\n            </td>\n          </tr>\n        </table>\n\n        <div ng-if=\"showingNodeInfo\">\n          <h5>Score calculation</h5>\n          <p ng-bind-html=\"currentNodeInfo\"></p>\n        </div>\n\n        <br>\n\n        <div class=\"closed-section\"></div>\n        <!--fun-metric-chart chart-name=\"currentChartName\" model-name=\"currentMetricModelName\"></fun-metric-chart-->\n      </div>\n    </div>\n    <div ng-switch-when=\"showingNonAtomicMetric\">\n      <!-- div style=\"padding-bottom: 10px;\"><h4>Aspect: {{ currentNode.chartName }}</h4></div-->\n      <div>\n        <table>\n          <tr>\n            <td>\n                                    <span id=\"score-table-parent\" class=\"score-card\">\n                                        <span id=\"score-table-child\">{{ currentNode.goodness }}\n                                        </span>\n                                    </span>\n            </td>\n            <td valign=\"top\" align=\"left\">\n                                <span id=\"score-table-info-icon\">\n                                    <i class=\"fa fa-info-circle\" style=\"padding: 2px\"\n                                       ng-click=\"showNodeInfoClick(currentNode)\">\n                                    </i>\n                                </span>\n            </td>\n          </tr>\n        </table>\n        <div ng-if=\"showingContainerNodeInfo\">\n          <br>\n          <h5>Children</h5>\n          <div ng-if=\"currentNode\">\n            <table class=\"table table-nonfluid\">\n              <tr>\n                <th>Aspect</th>\n                <th>Weight</th>\n                <th>Last score</th>\n                <th>Weight * Last Score</th>\n              </tr>\n              <tr ng-repeat=\"(childId, info) in currentNode.children\">\n                <td>{{ metricMap[childId].chartName }}</td>\n                <td>\n                  <p ng-click=\"editingWeightClick(info)\" ng-if=\"!info.editing\">{{ info.weight }}</p>\n                  <span ng-if=\"info.editing\">\n                                        <input style=\"padding-right: 10px\" type=\"number\" ng-model=\"info.editingWeight\">\n                                        <button style=\"border: 1px solid black;overflow: hidden; padding-left: 10px;\"\n                                                class=\"btn btn-sm\"\n                                                ng-click=\"submitWeightClick(currentNode, childId, info)\">&#10003;</button>\n                                        <button style=\"border: 1px solid black;\" class=\"btn btn-sm\"\n                                                ng-click=\"closeEditingWeightClick(info)\">&#10060;</button>\n                                    </span>\n                </td>\n                <td>\n                  {{ currentNode.childrenScoreMap[childId] | number: 1}}\n                </td>\n                <td>\n                  {{ info.weight }} * {{ currentNode.childrenScoreMap[childId] |\n                  number: 1 }} = {{ info.weight * currentNode.childrenScoreMap[childId]\n                  | number: 1 }}\n                </td>\n                <!-- td>{{ childId }}</td -->\n              </tr>\n              <tr>\n                <td></td>\n                <td></td>\n                <td></td>\n                <td>Total ~ {{ getScoreTotal(currentNode) | number: 1}}</td>\n              </tr>\n              <tr>\n                <td></td>\n                <td></td>\n                <td></td>\n                <td>Sum of child weights = {{ getSumChildWeights (currentNode.children) }}</td>\n              </tr>\n              <tr>\n                <td></td>\n                <td></td>\n                <td></td>\n                <td>Score ~ {{ getScoreTotal(currentNode) | number: 1}} / {{ getSumChildWeights(currentNode.children) }}\n                  = {{ getScoreTotal(currentNode) /  getSumChildWeights(currentNode.children) | number: 1}}</td>\n              </tr>\n            </table>\n          </div>\n        </div>\n      </div>\n      <br>\n      <div class=\"closed-section\"></div>\n      <!--fun-metric-chart chart-name=\"currentChartName\" model-name=\"currentMetricModelName\"></fun-metric-chart-->\n\n      <br>\n      <br>\n      <!--<div class=\"closed-section\"></div>-->\n      <div ng-if=\"grid.length\">\n        <table class=\"table\" ng-if=\"grid\">\n          <tr ng-repeat=\"row in grid track by $index\">\n            <td ng-repeat=\"node in row track by $index\" style=\"width: 50%\">\n              <!--fun-metric-chart\n                chart-name=\"node.name\"\n                model-name=\"node.metricModelName\"\n                atomic=\"atomic\"\n                chart-only=\"true\"\n                wait-time=\"(($parent.$index * numGridColumns) + $index) * 1000\">\n              </fun-metric-chart-->\n            </td>\n          </tr>\n        </table>\n        <div class=\"closed-section\"></div>\n      </div>\n    </div>\n  </div>\n\n\n</div>\n\n"

/***/ }),

/***/ "./src/app/performance/performance.component.ts":
/*!******************************************************!*\
  !*** ./src/app/performance/performance.component.ts ***!
  \******************************************************/
/*! exports provided: PerformanceComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "PerformanceComponent", function() { return PerformanceComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common */ "./node_modules/@angular/common/fesm5/common.js");
/* harmony import */ var _services_api_api_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../services/api/api.service */ "./src/app/services/api/api.service.ts");
/* harmony import */ var _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../services/logger/logger.service */ "./src/app/services/logger/logger.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var Node = /** @class */ (function () {
    function Node() {
    }
    return Node;
}());
var FlatNode = /** @class */ (function () {
    function FlatNode() {
    }
    return FlatNode;
}());
var PerformanceComponent = /** @class */ (function () {
    function PerformanceComponent(location, apiService, loggerService) {
        var _this = this;
        this.location = location;
        this.apiService = apiService;
        this.loggerService = loggerService;
        this.dag = null;
        this.nodeMap = {};
        this.lastGuid = 0;
        this.flatNodes = [];
        this.getNodeFromData = function (data) {
            var newNode = {
                info: data.description,
                label: data.chart_name,
                collapsed: true,
                metricId: data.metric_id,
                hide: true,
                leaf: data.leaf,
                chartName: data.chart_name,
                metricModelName: data.metric_model_name,
                childrenWeights: JSON.parse(data.children_weights),
                children: {},
                lineage: [],
                numChildDegrades: data.last_num_degrades,
                positive: data.positive,
                numChildren: 0,
                numChildrenPassed: data.num_children_passed,
                numChildrenFailed: data.last_num_build_failed,
                lastBuildStatus: data.last_build_status,
                status: true
            };
            _this.metricMap[newNode.metricId] = { chartName: newNode.chartName };
            if (newNode.info === "") {
                newNode.info = "<p>Please update the description</p>";
            }
            //     let dateRange = this.getDateRange();
            //     let fromDate = dateRange[0];
            //     let toDate = dateRange[1];
            //     return this.fetchScores(data.metric_id, fromDate.toISOString(), toDate.toISOString()).then((scoreData) => {
            //         newNode.childrenScoreMap = scoreData["children_score_map"];
            //         this.evaluateScores(newNode, scoreData["scores"]);
            //         newNode.childrenWeights.forEach((info, childId) => {
            //             newNode.children[childId] = {weight: newNode.childrenWeights[childId], editing: false};
            //         });
            //
            //         if (newNode.lastBuildStatus === "PASSED") {
            //             newNode.status = true;
            //         } else {
            //             newNode.status = false;
            //         }
            //
            //         let newNodeChildrenIds = JSON.parse(data.children);
            //         if (newNodeChildrenIds.length > 0) {
            //             newNode.numChildren = newNodeChildrenIds.length;
            //         }
            return newNode;
            //     });
            //
            //
        };
        this.guid = function () {
            function s4() {
                return Math.floor((1 + Math.random()) * 0x10000)
                    .toString(16)
                    .substring(1);
            }
            return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
        };
        this.expandNode = function (node, all) {
            node.collapsed = false;
            if (node.hasOwnProperty("numChildren") && (node.numChildren > 0)) {
                var thisNode = node;
                // Fetch children ids
                // return this.fetchMetricInfoById(node).then((data) => {
                //     console.log("Fetching Metrics Info for node:" + node.metricId);
                //     node.hide = false;
                //     let childrenIds = JSON.parse(data.children);
                //     return this._insertNewNode(node, childrenIds, all, node.childrenFetched).then(() => {
                //         console.log("Inserted: " + node.chartName);
                //         node.childrenFetched = true;
                //         return null;
                //     });
                //
                // });
            }
            else {
                return null;
            }
            //node.hide = false;
        };
    }
    PerformanceComponent.prototype.ngOnInit = function () {
        // this.getLastStatusUpdateTime();
        this.numGridColumns = 2;
        this.data = [['hi', 'hello'], ['how', 'are'], ['you', 'its'], ['been', 'a'], ['long', 'time'], ['also', 'when'], ['where', 'how'], ['are', 'we'], ['meeting', 'if'], [1, 2], [3, 4]];
        this.headers = ['Names', 'Numbers'];
        this.fetchDag();
        if (window.screen.width <= 1441) {
            this.numGridColumns = 2;
        }
    };
    PerformanceComponent.prototype.getGuid = function () {
        this.lastGuid++;
        return this.lastGuid;
    };
    PerformanceComponent.prototype.fetchDag = function () {
        var _this = this;
        // Fetch the DAG
        var payload = { metric_model_name: "MetricContainer", chart_name: "Total" };
        this.apiService.post("/metrics/dag", payload).subscribe(function (response) {
            _this.dag = response.data;
            _this.walkDag(_this.dag);
            var i = 0;
        }, function (error) {
            _this.loggerService.error("fetchDag");
        });
    };
    PerformanceComponent.prototype.getNodeFromEntry = function (metricId, dagEntry) {
        var node = new Node();
        node.metricId = metricId;
        node.chartName = dagEntry.chart_name;
        node.metricModelName = dagEntry.metric_model_name;
        node.numLeaves = dagEntry.num_leaves;
        node.numChildrenDegrades = dagEntry.last_num_degrades;
        node.lastNumBuildFailed = dagEntry.last_num_build_failed;
        return node;
    };
    PerformanceComponent.prototype.addNodeToMap = function (metricId, node) {
        this.nodeMap[metricId] = node;
    };
    PerformanceComponent.prototype.getNewFlatNode = function (node) {
        var newFlatNode = new FlatNode();
        newFlatNode.gUid = this.getGuid();
        newFlatNode.node = node;
        newFlatNode.hide = true;
        newFlatNode.collapsed = true;
        return newFlatNode;
    };
    PerformanceComponent.prototype.walkDag = function (dagEntry) {
        var _this = this;
        this.loggerService.log(dagEntry);
        var _loop_1 = function (metricId) {
            var numMetricId = Number(metricId); // TODO, why do we need this conversion
            var nodeInfo = dagEntry[numMetricId];
            var newNode = this_1.getNodeFromEntry(numMetricId, dagEntry[numMetricId]);
            this_1.addNodeToMap(numMetricId, newNode);
            this_1.flatNodes.push(this_1.getNewFlatNode(newNode));
            this_1.loggerService.log('Node:' + nodeInfo.chart_name);
            if (!nodeInfo.leaf) {
                var children = nodeInfo.children;
                children.forEach(function (cId) {
                    //let childEntry: {[childId: number]: object} = {cId: nodeInfo.children_info[Number(childId)]};
                    var childEntry = (_a = {}, _a[cId] = nodeInfo.children_info[Number(cId)], _a);
                    _this.walkDag(childEntry);
                    var _a;
                });
            }
        };
        var this_1 = this;
        for (var metricId in dagEntry) {
            _loop_1(metricId);
        }
    };
    PerformanceComponent.prototype.setValues = function (pageNumber) {
        this.data = [['hi', 'hello'], ['how', 'are']];
        this.headers = ['Names', 'Numbers'];
    };
    PerformanceComponent.prototype.goBack = function () {
        this.location.back();
    };
    PerformanceComponent.prototype.getLastStatusUpdateTime = function () {
        var _this = this;
        this.apiService.get('/common/time_keeper/' + "last_status_update").subscribe(function (data) {
            _this.lastStatusUpdateTime = data;
        }, function (error) {
        });
    };
    PerformanceComponent.prototype.fetchRootMetricInfo = function (chartName, metricModelName) {
        var _this = this;
        var payload = { "metric_model_name": metricModelName, chart_name: chartName };
        this.apiService.post('/metrics/chart_info', payload).subscribe(function (data) {
            return data;
        }, function (error) {
            _this.loggerService.error("fetchRootMetricInfo");
        });
    };
    PerformanceComponent.prototype.populateNodeInfoCache = function (data) {
        var _this = this;
        if (!(data.metric_id in this.cachedNodeInfo)) {
            this.cachedNodeInfo[data.metric_id] = data;
        }
        data.children_info.forEach(function (value, key) {
            _this.cachedNodeInfo[key] = value;
            value.children_info.forEach(function (v2, key2) {
                _this.populateNodeInfoCache(v2);
            });
        });
    };
    PerformanceComponent.prototype.counter = function (i) {
        return new Array(i);
    };
    PerformanceComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-performance',
            template: __webpack_require__(/*! ./performance.component.html */ "./src/app/performance/performance.component.html"),
            styles: [__webpack_require__(/*! ./performance.component.css */ "./src/app/performance/performance.component.css")]
        }),
        __metadata("design:paramtypes", [_angular_common__WEBPACK_IMPORTED_MODULE_1__["Location"],
            _services_api_api_service__WEBPACK_IMPORTED_MODULE_2__["ApiService"],
            _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_3__["LoggerService"]])
    ], PerformanceComponent);
    return PerformanceComponent;
}());

//
//     this.clearNodeInfoCache = () => {
//         this.cachedNodeInfo = {};
//     };
//
//
//
//
//
//
//
//     this.getIndex = (node) => {
//         let index = this.flatNodes.map(function(x) {return x.guid;}).indexOf(node.guid);
//         return index;
//     };
//
//     this.getNode = (guid) => {
//         return this.flatNodes[this.getIndex({guid: guid})];
//     };
//
//     this.expandAllNodes = () => {
//         this.flatNodes.forEach((node) => {
//             this.expandNode(node, true);
//         });
//         this.collapsedAll = false;
//         this.expandedAll = true;
//     };
//
//     this.collapseAllNodes = () => {
//         this.collapseNode(this.flatNodes[0]);
//         this.expandedAll = false;
//         this.collapsedAll = true;
//     };
//
//     this.getDateBound = (dt, lower) => {
//         let newDay = new Date(dt);
//         if (lower) {
//             newDay.setHours(0, 0, 1);
//         } else {
//             newDay.setHours(23, 59, 59);
//         }
//
//         return newDay;
//     };
//
//     function isSameDay(d1, d2) {
//           return d1.getFullYear() === d2.getUTCFullYear() &&
//             d1.getUTCMonth() === d2.getUTCMonth() &&
//             d1.getUTCDate() === d2.getUTCDate();
//     }
//
//     this.getYesterday = (today) => {
//         let yesterday = new Date(today);
//         yesterday = yesterday.setDate(yesterday.getDate() - 1);
//         return yesterday;
//     };
//
//
//     this.getDateRange = () => {
//         let today = new Date();
//         console.log(today);
//         let startMonth = 4 - 1;
//         let startDay = 1;
//         let startMinute = 59;
//         let startHour = 23;
//         let startSecond = 1;
//         let fromDate = new Date(today.getFullYear(), startMonth, startDay, startHour, startMinute, startSecond);
//         fromDate = this.getDateBound(fromDate, true);
//         // console.log(fromDate);
//         // console.log(this.getDateBound(fromDate, true));
//         // console.log(this.getDateBound(fromDate, false));
//
//         let yesterday = this.getYesterday(today);
//         let toDate = new Date(yesterday);
//         toDate = this.getDateBound(toDate, false);
//         //let fromDate = new Date();
//         // fromDate.setDate(toDate.getDate() - 7);
//         // fromDate = this.getDateBound(fromDate, true);
//         return [fromDate, toDate];
//
//     };
//
//
//
//     this.fetchScores = (metricId, fromDate, toDate) => {
//         let payload = {};
//         payload.metric_id = metricId;
//         payload.date_range = [fromDate, toDate];
//         return commonService.apiPost('/metrics/scores', payload).then((data) => {
//             return data;
//         });
//     };
//
//
//     this.getSumChildWeights = (children) => {
//         let sumOfWeights = 0;
//         angular.forEach(children, (info, childId) => {
//             sumOfWeights += info.weight;
//         });
//         return sumOfWeights;
//     };
//
//     this.getScoreTotal = (currentNode) => {
//         let children = currentNode.children;
//         let scoreTotal = 0;
//
//
//         angular.forEach(children, (info, childId) => {
//             scoreTotal += info.weight * currentNode.childrenScoreMap[childId];
//         });
//
//         let lastDate = new Date(this.validDates.slice(-1)[0] * 1000);
//         let lastDateLower = this.getDateBound(lastDate, true);
//         let lastDateUpper = this.getDateBound(lastDate, false);
//
//
//
//
//         return scoreTotal;
//     };
//
//     this.evaluateScores = (node, scores) => {
//
//         let keys = Object.keys(scores);
//         let sortedKeys = keys.sort();
//         if (node.chartName === "Total") {
//             this.validDates = sortedKeys;
//         }
//
//         if (Object.keys(scores).length) {
//
//             let mostRecentDateTimestamp = sortedKeys.slice(-1)[0];
//             let mostRecentDate = new Date(mostRecentDateTimestamp * 1000);
//             console.log(mostRecentDate);
//             console.log(scores[mostRecentDateTimestamp].score);
//             /*
//             let dateRange = this.getDateRange();
//             let fromDate = dateRange[0].getTime()/1000;
//             let toDate = dateRange[1].getTime()/1000;
//             let lastEntry = scores[toDate].score;*/
//         }
//         let goodnessValues = [];
//         sortedKeys.forEach((key) => {
//             goodnessValues.push(scores[key].score);
//         });
//
//         // console.log("Goodness values: " + goodnessValues);
//
//         node.goodnessValues = goodnessValues;
//         try {
//                 node.goodness = Number(goodnessValues[goodnessValues.length - 1].toFixed(1));
//         } catch (e) {
//
//         }
//
//         node.childrenGoodnessMap = {};
//         node.trend = "flat";
//         if (goodnessValues.length > 1) {
//             let penultimateGoodness = Number(goodnessValues[goodnessValues.length - 2].toFixed(1));
//             if (penultimateGoodness > node.goodness) {
//                 node.trend = "down";
//             } else if (penultimateGoodness < node.goodness) {
//                 node.trend = "up";
//             }
//             if (Number(goodnessValues[goodnessValues.length - 1].toFixed(1)) === 0) {
//                 node.trend = "down";
//             }
//         }
//         console.log("Node: " + node.chartName + " Goodness: " + node.goodness);
//     };
//
//     this.evaluateGoodness = (node, goodness_values, children_goodness_map) => {
//         if (goodness_values.length) {
//             try {
//                 node.goodness = Number(goodness_values[goodness_values.length - 1].toFixed(1));
//             } catch (e) {
//             }
//             node.goodnessValues = goodness_values;
//             node.childrenGoodnessMap = children_goodness_map;
//             node.trend = "flat";
//             let penultimateGoodness = Number(goodness_values[goodness_values.length - 2].toFixed(1));
//             if (penultimateGoodness > node.goodness) {
//                 node.trend = "down";
//             } else if (penultimateGoodness < node.goodness) {
//                 node.trend = "up";
//             }
//             if (Number(goodness_values[goodness_values.length - 1].toFixed(1)) === 0) {
//                 node.trend = "down";
//             }
//         }
//     };
//
//     this.getLastElement = (array) => {
//         let result = null;
//         if (array.length) {
//             result = array[array.length - 1];
//         }
//         return result;
//     };
//
//     this.setCurrentChart = (node) => {
//         this.mode = "showingAtomicMetric";
//         this.currentChartName = node.chartName;
//         this.currentMetricModelName = node.metricModelName;
//         this.currentNode = node;
//     };
//
//     this.showNodeInfoClick = (node) => {
//         if(this.currentMetricModelName === 'MetricContainer') {
//             this.showingContainerNodeInfo = !this.showingContainerNodeInfo;
//         }
//         else {
//             this.showingNodeInfo = !this.showingNodeInfo;
//             this.currentNodeInfo = null;
//             if (node.positive) {
//                 this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(last actual value/expected value) * 100&nbsp)/n";
//             } else {
//                 this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(expected value/last actual value) * 100&nbsp)/n";
//             }
//             this.currentNodeInfo += "&nbsp, where n is the number of data-sets";
//         }
//     };
//
//
//
//
//     this.getChildWeight = (node, childMetricId) => {
//         if (node.hasOwnProperty("childrenWeights")) {
//             return node.childrenWeights[childMetricId];
//         } else {
//             return 0;
//         }
//     };
//
//     this.editDescriptionClick = () => {
//         this.editingDescription = true;
//     };
//
//
//     this.closeEditingDescriptionClick = () => {
//         this.editingDescription = false;
//     };
//
//     this.openAtomicTab = () => {
//         let url = "/metrics/atomic/" + this.currentChartName + "/" + this.currentMetricModelName;
//         $window.open(url, '_blank');
//     };
//
//     this.submitDescription = (node) => {
//         let payload = {};
//         payload["metric_model_name"] = node.metricModelName;
//         payload["chart_name"] = node.chartName;
//         payload["description"] = this.inner.nonAtomicMetricInfo;
//
//         // TODO: Refresh cache
//         commonService.apiPost('/metrics/update_chart', payload, "EditDescription: Submit").then((data) => {
//             if (data) {
//                 alert("Submitted");
//             } else {
//                 alert("Submission failed. Please check alerts");
//             }
//         });
//         this.editingDescription = false;
//
//     };
//
//     this.tooltipFormatter = (x, y) => {
//         let softwareDate = "Unknown";
//         let hardwareVersion = "Unknown";
//         let sdkBranch = "Unknown";
//         let gitCommit = "Unknown";
//         let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
//         let match = r.exec(x);
//         let key = "";
//         if (match) {
//             key = match[1];
//         }
//         let s = "";
//
//         if (key in this.buildInfo) {
//             softwareDate = this.buildInfo[key]["software_date"];
//             hardwareVersion = this.buildInfo[key]["hardware_version"];
//             sdkBranch = this.buildInfo[key]["fun_sdk_branch"]
//             s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
//             s += "<b>Software date:</b> " + softwareDate + "<br>";
//             s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
//             s += "<b>Git commit:</b> " + this.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "")  + "<br>";
//             s += "<b>Value:</b> " + y + "<br>";
//         } else {
//             s += "<b>Value:</b> " + y + "<br>";
//         }
//
//         return s;
//     };
//
//
//     this.fetchMetricInfoById = (node) => {
//         let thisNode = node;
//         let p1 = {metric_id: node.metricId};
//         if (node.metricId in this.cachedNodeInfo) {
//             return $q.resolve(this.cachedNodeInfo[node.metricId]);
//         }
//         return commonService.apiPost('/metrics/metric_info', p1).then((data) => {
//            return data;
//         });
//     };
//
//
//     this.testClick = function () {
//         console.log("testClick");
//         console.log(ctrl.f);
//     };
//
//     this.showInfoClick = (node) => {
//         node.showInfo = !node.showInfo;
//     };
//
//     this.getConsolidatedTrend = (node) => {
//         let numTrendDown = 0;
//
//         if (node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids.forEach((childGuid) => {
//                 let child = this.flatNodes[this.getIndex({guid: childGuid})];
//                 numTrendDown += this.getConsolidatedTrend(child);
//             });
//         } else {
//             if (node.trend === "down") {
//                 numTrendDown += 1;
//             }
//         }
//         return numTrendDown;
//     };
//
//     this.getStatusHtml = (node) => {
//         let s = "";
//         if (node.leaf) {
//             if (node.hasOwnProperty("status")) {
//                 if (node.status !== true) {
//                     s = "Bld: <label class=\"label label-danger\">FAILED</label>";
//                 }
//                 if ((!node.hasOwnProperty("numChildren") && (!node.leaf)) || ((node.numChildren === 0) && !node.leaf)) {
//                     s = "<p style='background-color: white' class=\"\">No Data</p>";
//                 }
//             }
//         } else {
//
//
//
//             //s = "<p><span style='color: green'>&#10003;:</span><b>" + numTrendUp + "</b>" + "&nbsp" ;
//             //s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>";
//             /*if (node.chartName === "BLK_LSV: Latency") {
//                 let u = 0;
//             }*/
//
//             if (node.numChildDegrades) {
//                 s += "<span style='color: red'><i class='fa fa-arrow-down aspect-trend-icon fa-icon-red'>:</i></span>" + node.numChildDegrades + "";
//             }
//             if (node.numChildrenFailed) {
//                 if (node.numChildDegrades) {
//                     s += ",&nbsp";
//                 }
//                 s += "<i class='fa fa-times fa-icon-red'>:</i>" + "<span style='color: black'>" + node.numChildrenFailed + "</span>";
//             }
//         }
//         return s;
//     };
//
//     this.getTrendHtml = (node) => {
//         let s = "";
//         if (node.hasOwnProperty("trend")) {
//             if (node.trend === "up") {
//                 s = "<icon class=\"fa fa-arrow-up aspect-trend-icon fa-icon-green\"></icon>&nbsp";
//             } else if (node.trend === "down") {
//                 s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>&nbsp;";
//             }
//             else if (node.trend === "flat") {
//                 s = "<icon class=\"fa fa-arrow-down aspect-trend-icon\" style=\"visibility: hidden;\"></icon>&nbsp;";
//             }
//         }
//         return s;
//     };
//
//     this.isLeafsParent = (node) => {
//         let isLeafParent = false; // Parent of a leaf
//         if (node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids.forEach((childGuid) => {
//                 let child = this.flatNodes[this.getIndex({guid: childGuid})];
//                 if (child.leaf) {
//                     isLeafParent = true;
//                 }
//             });
//         }
//         return isLeafParent;
//     };
//
//     this.showNonAtomicMetric = (node) => {
//         this.resetGrid();
//         this.mode = "showingNonAtomicMetric";
//         this.currentNode = node;
//         this.currentChartName = node.chartName;
//         this.currentMetricModelName = "MetricContainer";
//         this.expandNode(node).then(() => {
//
//             //this.mode = "showingNonAtomicMetric";
//             this._setupGoodnessTrend(node);
//             this.inner.nonAtomicMetricInfo = node.info;
//             //this.currentNode = null;
//            // this.currentNode = node;
//             // let payload = {
//             //     metric_model_name: "MetricContainer",
//             //     chart_name: node.chartName
//             // };
//             //this.currentChartName = node.chartName;
//             //this.currentMetricModelName = "MetricContainer";
//             console.log("Before getting leaves");
//             if ((node.chartName === "All metrics") || (!this.isLeafsParent(node))) {
//                 return $q.resolve(null);
//             } else {
//                 return $q.resolve(null); // Disable for now
//                 // commonService.apiPost('/metrics/get_leaves', payload, 'test').then((leaves) => {
//                 //
//                 //     let flattenedLeaves = {};
//                 //     this.flattenLeaves("", flattenedLeaves, leaves);
//                 //     $timeout(()=> {
//                 //         this.prepareGridNodes(flattenedLeaves);
//                 //     }, 1000);
//                 //
//                 //     console.log(angular.element($window).width());
//                 //
//                 // });
//
//             }
//
//         });
//
//
//     };
//
//     this.flattenLeaves = function (parentName, flattenedLeaves, node) {
//         let myName = node.name;
//         if (parentName !== "") {
//             myName = parentName + " > " + node.name;
//         }
//         if (!node.leaf) {
//             node.children.forEach((child) => {
//                 this.flattenLeaves(myName, flattenedLeaves, child);
//             });
//         } else {
//             node.lineage = parentName;
//             let newNode = {name: node.name, id: node.id, metricModelName: node.metric_model_name};
//             flattenedLeaves[newNode.id] = newNode;
//         }
//     };
//
//     this.resetGrid = () => {
//         this.grid = [];
//     };
//
//     this.prepareGridNodes = (flattenedNodes) => {
//         let maxRowsInMiniChartGrid = 10;
//         console.log("Prepare Grid nodes");
//         let tempGrid = [];
//         let rowIndex = 0;
//         Object.keys(flattenedNodes).forEach((key) => {
//             if (rowIndex < maxRowsInMiniChartGrid) {
//                 if (tempGrid.length - 1 < rowIndex) {
//                     tempGrid.push([]);
//                 }
//                 tempGrid[rowIndex].push(flattenedNodes[key]);
//                 if (tempGrid[rowIndex].length === this.numGridColumns) {
//                     rowIndex++;
//                 }
//             }
//         });
//         this.grid = tempGrid;
//
//     };
//
//     this._setupGoodnessTrend = (node) => {
//         let values = [{
//                 data: node.goodnessValues
//             }];
//         this.goodnessTrendValues = null;
//         $timeout (() => {
//             this.goodnessTrendValues = values;
//         }, 1);
//
//         this.charting = true;
//
//         this.goodnessTrendChartTitle = node.chartName;
//     };
//
//     this.getChildrenGuids = (node) => {
//         return node.childrenGuids;
//     };
//
//     this.showGoodnessTrend = (node) => {
//         this.mode = "showingGoodnessTrend";
//         this._setupGoodnessTrend(node);
//     };
//
//     this.getIndentHtml = (node) => {
//         let s = "";
//         if (node.hasOwnProperty("indent")) {
//             for(let i = 0; i < node.indent - 1; i++) {
//                 s += "<span style=\"color: white\">&rarr;</span>";
//             }
//             if (node.indent)
//                 s += "<span>&nbsp;&nbsp;</span>";
//         }
//
//         return s;
//     };
//
//     this.editingWeightClick = (info) => {
//         info.editing = true;
//         info.editingWeight = info.weight;
//     };
//
//     this.submitWeightClick = (node, childId, info) => {
//         let payload = {};
//         payload.metric_id = node.metricId;
//         payload.lineage = node.lineage;
//         payload.child_id = childId;
//         payload.weight = info.editingWeight;
//         commonService.apiPost('/metrics/update_child_weight', payload).then((data) => {
//             info.weight = info.editingWeight;
//             this.clearNodeInfoCache();
//             if (node.hasOwnProperty("lineage") && node.lineage.length > 0) {
//                 this.refreshNode(this.getNode(node.lineage[0]));
//             } else {
//                 this.refreshNode(node);
//             }
//         });
//         info.editing = false;
//     };
//
//     this.closeEditingWeightClick = (info) => {
//         info.editing = false;
//     };
//
//
//     this.collapseNode = (node) => {
//         if (node.hasOwnProperty("numChildren")) {
//             this.collapseBranch(node);
//         }
//         node.collapsed = true;
//     };
//
//
//
//     this._insertNewNode = (node, childrenIds, all, alreadyInserted) => {
//         if (childrenIds.length <= 0) {
//             return;
//         }
//         let thisNode = node;
//         let thisAll = all;
//         let childId = childrenIds.pop();
//         let thisChildrenIds = childrenIds;
//         let p1 = {metric_id: childId};
//         if (!node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids = [];
//         }
//
//         return this.fetchMetricInfoById({metricId: childId}).then((data) => {
//             if (!alreadyInserted) {
//                 console.log("!alreadyInserted");
//                 return this.getNodeFromData(data).then((newNode) => {
//                     newNode.guid = this.guid();
//                     thisNode.lineage.forEach((ancestor) => {
//                        newNode.lineage.push(ancestor);
//                     });
//                     newNode.lineage.push(thisNode.guid);
//                     console.log("Added childGuid for node:" + node.chartName);
//                     node.childrenGuids.push(newNode.guid);
//
//                     newNode.indent = thisNode.indent + 1;
//                     let index = this.getIndex(thisNode);
//                     this.flatNodes.splice(index + 1, 0, newNode);
//                     this._insertNewNode(thisNode, thisChildrenIds, thisAll);
//                     newNode.hide = false;
//                     if (thisAll) {
//                         this.expandNode(newNode, thisAll);
//                     }
//                 });
//
//             } else {
//                 console.log("alreadyInserted");
//                 node.childrenGuids.forEach((childGuid) => {
//                    let childNode = this.flatNodes[this.getIndex({guid: childGuid})];
//                    //let childrenIds = JSON.parse(data.children);
//                    childNode.hide = false;
//
//                 });
//
//                 this._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
//             }
//             return $q.resolve(null);
//         });
//
//
//     };
//
//     this.refreshNode = (node) => {
//         let payload = {metric_id: node.metricId};
//         commonService.apiPost('/metrics/metric_info', payload).then((data) => {
//             this.populateNodeInfoCache(data);
//             this.evaluateGoodness(node, data.goodness_values, data.children_goodness_map);
//             this._setupGoodnessTrend(node);
//         });
//         if (node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids.forEach((childGuid) => {
//                 this.refreshNode(this.getNode(childGuid));
//             });
//         }
//     };
//
//
//     this.collapseBranch = (node, traversedNodes) => {
//         let thisIndex = this.getIndex(node);
//         if (node.hasOwnProperty("numChildren")) {
//             this.hideChildren(node, true);
//             /*
//             for(let i = 1; i <= node.numChildren; i++) {
//                 if (!node.collapsed) {
//                     traversedNodes += this.collapseBranch(this.flatNodes[thisIndex + traversedNodes + 2]);
//                     this.flatNodes[thisIndex + traversedNodes + 1].collapsed = true;
//                     this.flatNodes[thisIndex + traversedNodes + 1].hide = true;
//                 }
//             }*/
//         }
//         return traversedNodes;
//     };
//
//     this.hideChildren = (node, root) => {
//         let totalHides = 0;
//         if (!node) {
//             return 0;
//         }
//         let thisIndex = this.getIndex(node);
//
//
//
//         if (node.hasOwnProperty("numChildren")) {
//             if (!node.childrenFetched) {
//                 return 0;
//             }
//
//             let nextIndex = thisIndex + 1;
//             if ((nextIndex >= this.flatNodes.length) && (!node.collapsed)) {
//                 console.log("Huh!");
//                 return 0;
//             }
//             for(let i = 1; i <= node.numChildren  && (nextIndex < this.flatNodes.length); i++) {
//                 let hides = 0;
//                 if (true) {
//                     hides += this.hideChildren(this.flatNodes[nextIndex], false);
//                 }
//
//                 this.flatNodes[nextIndex].collapsed = true;
//                 this.flatNodes[nextIndex].hide = true;
//                 totalHides += 1 + hides;
//                 nextIndex += hides + 1;
//
//             }
//         }
//         /*
//         if (!root) {
//             this.flatNodes[thisIndex].collapsed = true;
//             this.flatNodes[thisIndex].hide = true;
//             totalHides += 1;
//         }*/
//         return totalHides;
//     };
//
//     isNodeVisible = (node) => {
//         return !node.hide;
//     }
//
// }
//
//
//
//
//
//


/***/ }),

/***/ "./src/app/pipe/fun-table-filter.pipe.ts":
/*!***********************************************!*\
  !*** ./src/app/pipe/fun-table-filter.pipe.ts ***!
  \***********************************************/
/*! exports provided: FunTableFilterPipe */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "FunTableFilterPipe", function() { return FunTableFilterPipe; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};

var FunTableFilterPipe = /** @class */ (function () {
    function FunTableFilterPipe() {
    }
    FunTableFilterPipe.prototype.transform = function (items, filter) {
        console.log("Filter Pipe");
        if (!items || !filter) {
            return items;
        }
        return items.filter(function (item) {
            if (items.indexOf(item) < filter.size && filter.get(items.indexOf(item))) {
                return true;
            }
            return false;
        });
    };
    FunTableFilterPipe = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Pipe"])({
            name: 'funTableFilter',
            pure: true
        })
    ], FunTableFilterPipe);
    return FunTableFilterPipe;
}());



/***/ }),

/***/ "./src/app/services/api/api.service.ts":
/*!*********************************************!*\
  !*** ./src/app/services/api/api.service.ts ***!
  \*********************************************/
/*! exports provided: ApiResponse, ApiService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ApiResponse", function() { return ApiResponse; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ApiService", function() { return ApiService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/_esm5/index.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var ApiResponse = /** @class */ (function () {
    function ApiResponse(fields) {
        if (fields)
            Object.assign(this, fields);
    }
    return ApiResponse;
}());

var ApiService = /** @class */ (function () {
    function ApiService(httpClient) {
        this.httpClient = httpClient;
    }
    ApiService_1 = ApiService;
    ApiService.handleError = function (error) {
        var result = new ApiResponse();
        result.status = false;
        result.data = null;
        result.error_message = "Http Error: Status: " + error.status + " Text: " + error.statusText + " URL: " + error.url; // TODO: Improve this
        throw Object(rxjs__WEBPACK_IMPORTED_MODULE_3__["of"])(result);
    };
    ApiService.prototype.post = function (url, payload) {
        return this.httpClient.post(url, payload)
            .pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["map"])(function (response) {
            return response;
        }), Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["catchError"])(ApiService_1.handleError));
    };
    ApiService.prototype.get = function (url) {
        return this.httpClient.get(url)
            .pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["map"])(function (response) {
            return response;
        }), Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["catchError"])(ApiService_1.handleError));
    };
    ApiService = ApiService_1 = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root'
        }),
        __metadata("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_1__["HttpClient"]])
    ], ApiService);
    return ApiService;
    var ApiService_1;
}());



/***/ }),

/***/ "./src/app/services/logger/logger.service.ts":
/*!***************************************************!*\
  !*** ./src/app/services/logger/logger.service.ts ***!
  \***************************************************/
/*! exports provided: LogLevel, LogEntry, LoggerService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogLevel", function() { return LogLevel; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogEntry", function() { return LogEntry; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LoggerService", function() { return LoggerService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};

var LogLevel;
(function (LogLevel) {
    LogLevel[LogLevel["All"] = 0] = "All";
    LogLevel[LogLevel["Debug"] = 1] = "Debug";
    LogLevel[LogLevel["Info"] = 2] = "Info";
    LogLevel[LogLevel["Warn"] = 3] = "Warn";
    LogLevel[LogLevel["Error"] = 4] = "Error";
    LogLevel[LogLevel["Fatal"] = 5] = "Fatal";
    LogLevel[LogLevel["Off"] = 6] = "Off";
})(LogLevel || (LogLevel = {}));
var LogEntry = /** @class */ (function () {
    function LogEntry() {
        // Public properties
        this.entryDate = new Date();
        this.message = '';
        this.level = LogLevel.Debug;
        this.extraInfo = [];
        this.logWithDate = true;
    }
    LogEntry.prototype.buildLogString = function () {
        var ret = '';
        if (this.logWithDate) {
            ret = new Date() + ' - ';
        }
        ret += 'Type: ' + LogLevel[this.level];
        ret += ' - Message: ' + this.message;
        if (this.extraInfo.length) {
            ret += ' - Extra Info: ' + LogEntry.formatParams(this.extraInfo);
        }
        return ret;
    };
    LogEntry.formatParams = function (params) {
        var ret = params.join(',');
        if (params.some(function (p) { return typeof p === 'object'; })) {
            ret = '';
            for (var _i = 0, params_1 = params; _i < params_1.length; _i++) {
                var item = params_1[_i];
                ret += JSON.stringify(item) + ',';
            }
        }
        return ret;
    };
    return LogEntry;
}());

var LoggerService = /** @class */ (function () {
    function LoggerService() {
        // Public properties
        this.level = LogLevel.All;
        this.logWithDate = true;
    }
    LoggerService.prototype.shouldLog = function (level) {
        var ret = false;
        if (this.level !== LogLevel.Off && level >= this.level) {
            ret = true;
        }
        return ret;
    };
    LoggerService.prototype.debug = function (msg) {
        var optionalParams = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            optionalParams[_i - 1] = arguments[_i];
        }
        this.writeToLog(msg, LogLevel.Debug, optionalParams);
    };
    LoggerService.prototype.info = function (msg) {
        var optionalParams = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            optionalParams[_i - 1] = arguments[_i];
        }
        this.writeToLog(msg, LogLevel.Info, optionalParams);
    };
    LoggerService.prototype.warn = function (msg) {
        var optionalParams = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            optionalParams[_i - 1] = arguments[_i];
        }
        this.writeToLog(msg, LogLevel.Warn, optionalParams);
    };
    LoggerService.prototype.error = function (msg) {
        var optionalParams = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            optionalParams[_i - 1] = arguments[_i];
        }
        this.writeToLog(msg, LogLevel.Error, optionalParams);
    };
    LoggerService.prototype.fatal = function (msg) {
        var optionalParams = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            optionalParams[_i - 1] = arguments[_i];
        }
        this.writeToLog(msg, LogLevel.Debug, optionalParams);
    };
    LoggerService.prototype.log = function (msg) {
        var optionalParams = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            optionalParams[_i - 1] = arguments[_i];
        }
        this.writeToLog(msg, LogLevel.All, optionalParams);
    };
    LoggerService.prototype.writeToLog = function (msg, level, params) {
        if (this.shouldLog(level)) {
            var entry = new LogEntry();
            entry.message = msg;
            entry.level = level;
            entry.extraInfo = params;
            entry.logWithDate = this.logWithDate;
            console.log(entry);
        }
    };
    LoggerService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])()
    ], LoggerService);
    return LoggerService;
}());



/***/ }),

/***/ "./src/app/services/pager/pager.service.ts":
/*!*************************************************!*\
  !*** ./src/app/services/pager/pager.service.ts ***!
  \*************************************************/
/*! exports provided: PagerService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "PagerService", function() { return PagerService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};

var PagerService = /** @class */ (function () {
    function PagerService() {
    }
    PagerService.prototype.getPager = function (totalItems, currentPage, pageSize) {
        if (currentPage === void 0) { currentPage = 1; }
        if (pageSize === void 0) { pageSize = 10; }
        // calculate total pages
        var totalPages = Math.ceil(totalItems / pageSize);
        // ensure current page isn't out of range
        if (currentPage < 1) {
            currentPage = 1;
        }
        else if (currentPage > totalPages) {
            currentPage = totalPages;
        }
        var startPage, endPage;
        if (totalPages <= 10) {
            // less than 10 total pages so show all
            startPage = 1;
            endPage = totalPages;
        }
        else {
            // more than 10 total pages so calculate start and end pages
            if (currentPage <= 6) {
                startPage = 1;
                endPage = 10;
            }
            else if (currentPage + 4 >= totalPages) {
                startPage = totalPages - 9;
                endPage = totalPages;
            }
            else {
                startPage = currentPage - 5;
                endPage = currentPage + 4;
            }
        }
        // calculate start and end item indexes
        var startIndex = (currentPage - 1) * pageSize;
        var endIndex = Math.min(startIndex + pageSize - 1, totalItems - 1);
        // create an array of pages to ng-repeat in the pager control
        var pages = Array.from(Array((endPage + 1) - startPage).keys()).map(function (i) { return startPage + i; });
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
    };
    PagerService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root'
        })
    ], PagerService);
    return PagerService;
}());



/***/ }),

/***/ "./src/app/test/test.component.css":
/*!*****************************************!*\
  !*** ./src/app/test/test.component.css ***!
  \*****************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/test/test.component.html":
/*!******************************************!*\
  !*** ./src/app/test/test.component.html ***!
  \******************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<!--<p>-->\n  <!--test works!-->\n\n<!--</p>-->\n<!--<div class=\"jumbotron text-center\">-->\n  <!--<h1>My First Bootstrap Page</h1>-->\n  <!--<p>Resize this responsive page to see the effect!</p>-->\n<!--</div>-->\n\n<!--<div class=\"container\">-->\n  <!--<div class=\"row\">-->\n    <!--<div class=\"col-sm-4\">-->\n      <!--<h3>Column 1</h3>-->\n      <!--<p>Lorem ipsum dolor..</p>-->\n      <!--<p>Ut enim ad..</p>-->\n    <!--</div>-->\n    <!--<div class=\"col-sm-4\">-->\n      <!--<h3>Column 2</h3>-->\n      <!--<p>Lorem ipsum dolor..</p>-->\n      <!--<p>Ut enim ad..</p>-->\n    <!--</div>-->\n    <!--<div class=\"col-sm-4\">-->\n      <!--<h3>Column 3</h3>-->\n      <!--<p>Lorem ipsum dolor..</p>-->\n      <!--<p>Ut enim ad..</p>-->\n    <!--</div>-->\n  <!--</div>-->\n<!--</div>-->\n\n<!--<ul class=\"list-group\">-->\n  <!--<li class=\"list-group-item active\">Active item</li>-->\n  <!--<li class=\"list-group-item\">Second item</li>-->\n  <!--<li class=\"list-group-item\">Third item</li>-->\n<!--</ul>-->\n\n<!--<div class=\"container\">-->\n  <!--<h2>Card Image</h2>-->\n  <!--<p>Image at the top (card-img-top):</p>-->\n  <!--<div class=\"card\" style=\"width:400px\">-->\n    <!--<img class=\"card-img-top\" src=\"https://www.w3schools.com/bootstrap4/img_avatar1.png\" alt=\"Card image\" style=\"width:100%\">-->\n    <!--<div class=\"card-body\">-->\n      <!--<h4 class=\"card-title\">John Doe</h4>-->\n      <!--<p class=\"card-text\">Some example text some example text. John Doe is an architect and engineer</p>-->\n      <!--<a href=\"#\" class=\"btn btn-primary\">See Profile</a>-->\n    <!--</div>-->\n  <!--</div>-->\n  <!--<br>-->\n\n  <!--<p>Image at the bottom (card-img-bottom):</p>-->\n  <!--<div class=\"card\" style=\"width:400px\">-->\n    <!--<div class=\"card-body\">-->\n      <!--<h4 class=\"card-title\">Jane Doe</h4>-->\n      <!--<p class=\"card-text\">Some example text some example text. Jane Doe is an architect and engineer</p>-->\n      <!--<a href=\"#\" class=\"btn btn-primary\">See Profile</a>-->\n    <!--</div>-->\n    <!--<img class=\"card-img-bottom\" src=\"img_avatar6.png\" alt=\"Card image\" style=\"width:100%\">-->\n  <!--</div>-->\n<!--</div>-->\n<div class=\"card\">\n  <fun-metric-chart [chartName]=\"'Best time for 1 malloc/free (WU)'\" [modelName]=\"'AllocSpeedPerformance'\"></fun-metric-chart>\n\n</div>\n"

/***/ }),

/***/ "./src/app/test/test.component.ts":
/*!****************************************!*\
  !*** ./src/app/test/test.component.ts ***!
  \****************************************/
/*! exports provided: TestComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TestComponent", function() { return TestComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var TestComponent = /** @class */ (function () {
    function TestComponent() {
        this.yValues = [];
        this.xValues = [];
    }
    TestComponent.prototype.ngOnInit = function () {
        // let temp = [];
        // temp["name"] = 'series 1';
        // temp["data"] = [1,2,3,4,5];
        // this.yValues[0] = temp;
        this.yValues.push({ name: 'series 1', data: [1, 2, 3, 4, 5] });
        this.yValues.push({ name: 'series 2', data: [6, 7, 8, 9, 10] });
        this.yValues.push({ name: 'series 3', data: [11, 12, 13, 14, 15] });
        this.yValues.push({ name: 'series 4', data: [16, 17, 18, 19, 20] });
        this.yValues.push({ name: 'series 5', data: [21, 22, 23, 24, 25] });
        this.xValues.push([0, 1, 2, 3, 4]);
        this.title = "Funchart";
        this.xAxisLabel = "Date";
        this.yAxisLabel = "Range";
    };
    TestComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-test',
            template: __webpack_require__(/*! ./test.component.html */ "./src/app/test/test.component.html"),
            styles: [__webpack_require__(/*! ./test.component.css */ "./src/app/test/test.component.css")]
        }),
        __metadata("design:paramtypes", [])
    ], TestComponent);
    return TestComponent;
}());



/***/ }),

/***/ "./src/environments/environment.ts":
/*!*****************************************!*\
  !*** ./src/environments/environment.ts ***!
  \*****************************************/
/*! exports provided: environment */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "environment", function() { return environment; });
// This file can be replaced during build by using the `fileReplacements` array.
// `ng build ---prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.
var environment = {
    production: false
};
/*
 * In development mode, for easier debugging, you can ignore zone related error
 * stack frames such as `zone.run`/`zoneDelegate.invokeTask` by importing the
 * below file. Don't forget to comment it out in production mode
 * because it will have a performance impact when errors are thrown
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.


/***/ }),

/***/ "./src/main.ts":
/*!*********************!*\
  !*** ./src/main.ts ***!
  \*********************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser-dynamic */ "./node_modules/@angular/platform-browser-dynamic/fesm5/platform-browser-dynamic.js");
/* harmony import */ var _app_app_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./app/app.module */ "./src/app/app.module.ts");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./environments/environment */ "./src/environments/environment.ts");




if (_environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].production) {
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["enableProdMode"])();
}
Object(_angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__["platformBrowserDynamic"])().bootstrapModule(_app_app_module__WEBPACK_IMPORTED_MODULE_2__["AppModule"])
    .catch(function (err) { return console.log(err); });


/***/ }),

/***/ 0:
/*!***************************!*\
  !*** multi ./src/main.ts ***!
  \***************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(/*! /Users/ash/Desktop/Integration/fun_test/web/angular/qadashboard/src/main.ts */"./src/main.ts");


/***/ })

},[[0,"runtime","vendor"]]]);
//# sourceMappingURL=main.js.map