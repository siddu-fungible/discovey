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
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};




var routes = [
    { path: 'upgrade', component: _dashboard_dashboard_component__WEBPACK_IMPORTED_MODULE_2__["DashboardComponent"] },
    { path: 'upgrade/dashboard', component: _dashboard_dashboard_component__WEBPACK_IMPORTED_MODULE_2__["DashboardComponent"] },
    { path: 'upgrade/performance', component: _performance_performance_component__WEBPACK_IMPORTED_MODULE_3__["PerformanceComponent"] }
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
                _fun_table_fun_table_component__WEBPACK_IMPORTED_MODULE_9__["FunTableComponent"]
            ],
            imports: [
                _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__["BrowserModule"],
                _angular_common_http__WEBPACK_IMPORTED_MODULE_8__["HttpClientModule"],
                _app_routing_module__WEBPACK_IMPORTED_MODULE_6__["AppRoutingModule"],
                _angular_platform_browser_animations__WEBPACK_IMPORTED_MODULE_3__["BrowserAnimationsModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_2__["MatSortModule"]
            ],
            providers: [_services_api_api_service__WEBPACK_IMPORTED_MODULE_10__["ApiService"], _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_11__["LoggerService"]],
            bootstrap: [_app_component__WEBPACK_IMPORTED_MODULE_4__["AppComponent"]]
        })
    ], AppModule);
    return AppModule;
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

module.exports = "<title>QA Dashboard</title>\n<div>\n  My dashboard\n  <!--<app-performance></app-performance>-->\n</div>\n"

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

/***/ "./src/app/fun-table/fun-table.component.css":
/*!***************************************************!*\
  !*** ./src/app/fun-table/fun-table.component.css ***!
  \***************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".tableContainer {\n  margin: 5px;\n  padding: 5px;\n}\n"

/***/ }),

/***/ "./src/app/fun-table/fun-table.component.html":
/*!****************************************************!*\
  !*** ./src/app/fun-table/fun-table.component.html ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<p>\n  table works!\n</p>\n<!--<link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css\">-->\n<link href=\"https://gitcdn.github.io/bootstrap-toggle/2.2.2/css/bootstrap-toggle.min.css\" rel=\"stylesheet\">\n<script src=\"https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js\"></script>\n<div class=\"card tableContainer\">\n  <div>\n    <div>\n      <!-- items being paged -->\n      <table class=\"table\" matSort (matSortChange)=\"sortData($event)\">\n        <tr>\n          <th *ngFor=\"let header of headers; index as i\" mat-sort-header=\"{{i}}\">{{ header }}</th>\n        </tr>\n        <tr *ngFor=\"let item of pagedItems\">\n          <td *ngFor=\"let rowItems of item\">{{rowItems}}</td>\n        </tr>\n      </table>\n\n      <!-- pager -->\n      <ul *ngIf=\"pager.pages && pager.pages.length\" class=\"pagination\">\n        <li [ngClass]=\"{disabled:pager.currentPage === 1}\">\n          <a (click)=\"setPage(1)\">First</a>\n        </li>\n        <li [ngClass]=\"{disabled:pager.currentPage === 1}\">\n          <a (click)=\"setPage(pager.currentPage - 1)\">Previous</a>\n        </li>\n        <li *ngFor=\"let page of pager.pages\" [ngClass]=\"{active:pager.currentPage === page}\">\n          <a (click)=\"setPage(page)\">{{page}}</a>\n        </li>\n        <li [ngClass]=\"{disabled:pager.currentPage === pager.totalPages}\">\n          <a (click)=\"setPage(pager.currentPage + 1)\">Next</a>\n        </li>\n        <li [ngClass]=\"{disabled:pager.currentPage === pager.totalPages}\">\n          <a (click)=\"setPage(pager.totalPages)\">Last</a>\n        </li>\n      </ul>\n      <button (click)=\"editColumns()\" style=\"float: right\">Advanced</button>\n    </div>\n  </div>\n\n  <div *ngIf=\"hideShowColumns\">\n    <!--<form>-->\n      <!--<div *ngFor=\"let header of headers\">-->\n        <!--{{header}}<input bs-switch type=\"checkbox\"/>-->\n      <!--</div>-->\n      <div class=\"panel panel-default\">\n        <div class=\"panel-heading\">Columns</div>\n        <div class=\"panel-body\" *ngFor=\"let header of headers\">{{header}}</div>\n      </div>\n<div class=\"col-md-2\">\n\n        <h4>iOS7 Style</h4>\n\n        <div class=\"switch\">\n        <input id=\"cmn-toggle-4\" class=\"cmn-toggle cmn-toggle-round-flat\" type=\"checkbox\">\n        <label for=\"cmn-toggle-4\"></label>\n        </div>\n\n    </div>    <button (click)=\"submit()\">Submit</button>\n    <button (click)=\"editColumns()\" style=\"margin: 5px;\">Close</button>\n  </div>\n</div>\n"

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
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var FunTableComponent = /** @class */ (function () {
    function FunTableComponent(pagerService, logger) {
        this.pagerService = pagerService;
        this.logger = logger;
        this.hideShowColumns = false;
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
        this.logger.log("Open form is entered");
        this.hideShowColumns = !this.hideShowColumns;
    };
    FunTableComponent.prototype.submit = function () {
        this.logger.log("submitted the column change");
        this.hideShowColumns = false;
        //change the headers.
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
            styles: [__webpack_require__(/*! ./fun-table.component.css */ "./src/app/fun-table/fun-table.component.css")]
        }),
        __metadata("design:paramtypes", [_services_pager_pager_service__WEBPACK_IMPORTED_MODULE_1__["PagerService"], _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_2__["LoggerService"]])
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

module.exports = ""

/***/ }),

/***/ "./src/app/performance/performance.component.html":
/*!********************************************************!*\
  !*** ./src/app/performance/performance.component.html ***!
  \********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<p>\n  performance works!\n</p>\n<fun-table (nextPage)=\"setValues($event)\" [data]=\"data\"></fun-table>\n"

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



var PerformanceComponent = /** @class */ (function () {
    function PerformanceComponent(apiService, logger) {
        this.apiService = apiService;
        this.logger = logger;
        this.componentState = "Unknown";
        this.data = [];
        this.logger.log("Performance component init");
    }
    PerformanceComponent.prototype.ngOnInit = function () {
        var _this = this;
        this.data["rows"] = [['hi', 'hello'], ['how', 'are'], ['you', 'its'], ['been', 'a'], ['long', 'time'], ['also', 'when'], ['where', 'how'], ['are', 'we'], ['meeting', 'if'], ['hey', 'buddy'], ['let', 'go'], ['we', 'will']];
        this.data["headers"] = ['Names', 'Numbers'];
        this.data["all"] = true;
        this.data["totalLength"] = 12;
        this.data["currentPageIndex"] = 1;
        this.data["pageSize"] = 10;
        this.getLastStatusUpdateTime();
        this.numGridColumns = 2;
        if (window.screen.width <= 1441) {
            this.numGridColumns = 2;
        }
        this.mode = null;
        this.fetchJenkinsJobIdMap();
        this.flatNodes = [];
        this.metricMap = {};
        this.cachedNodeInfo = {};
        this.fetchRootMetricInfo("Total", "MetricContainer").then(function (data) {
            var metricId = data.metric_id;
            var p1 = { metric_id: metricId };
            _this.apiService.post('/metrics/metric_info', p1).subscribe(function (data) {
                _this.populateNodeInfoCache(data);
                var newNode = _this.getNodeFromData(data).then(function (newNode) {
                    newNode.guid = _this.guid();
                    newNode.hide = false;
                    newNode.indent = 0;
                    _this.flatNodes.push(newNode);
                    // this.expandNode(newNode);
                    _this.collapsedAll = true;
                });
            }, function (error) {
                console.log(error);
                _this.componentState = "Error";
            });
            return data;
        });
        this.goodnessTrendValues = null;
        this.inner = {};
        this.inner.nonAtomicMetricInfo = "";
        this.currentNodeChildrenGuids = null;
        this.validDates = null;
    };
    PerformanceComponent.prototype.getLastStatusUpdateTime = function () {
        var _this = this;
        this.apiService.get('/common/time_keeper/' + "last_status_update").subscribe(function (data) {
            _this.lastStatusUpdateTime = data;
        }, function (error) {
            console.log(error);
            _this.componentState = "Error";
        });
    };
    PerformanceComponent.prototype.fetchJenkinsJobIdMap = function () {
        var _this = this;
        this.apiService.get('/regression/jenkins_job_id_maps').subscribe(function (data) {
            _this.jenkinsJobIdMap = data;
            _this.apiService.get('/regression/build_to_date_map').subscribe(function (data) {
                _this.buildInfo = data;
            }, function (error) {
                console.log(error);
                _this.componentState = "Error";
            });
        }, function (error) {
            console.log(error);
            _this.componentState = "Error";
        });
    };
    PerformanceComponent.prototype.fetchRootMetricInfo = function (chartName, metricModelName) {
        var _this = this;
        var payload = { "metric_model_name": metricModelName, chart_name: chartName };
        return this.apiService.post('/metrics/chart_info', payload).subscribe(function (data) {
            return data;
        }, function (error) {
            console.log(error);
            _this.componentState = "Error";
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
    PerformanceComponent.prototype.guid = function () {
        function s4() {
            return Math.floor((1 + Math.random()) * 0x10000)
                .toString(16)
                .substring(1);
        }
        return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
    };
    PerformanceComponent.prototype.expandAllNodes = function () {
        var _this = this;
        this.flatNodes.forEach(function (node) {
            _this.expandNode(node, true);
        });
        this.collapsedAll = false;
        this.expandedAll = true;
    };
    PerformanceComponent.prototype.collapseAllNodes = function () {
        this.collapseNode(this.flatNodes[0]);
        this.expandedAll = false;
        this.collapsedAll = true;
    };
    ;
    PerformanceComponent.prototype.expandNode = function (node, all) {
        var _this = this;
        node.collapsed = false;
        if (node.hasOwnProperty("numChildren") && (node.numChildren > 0)) {
            var thisNode = node;
            return this.fetchMetricInfoById(node).then(function (data) {
                console.log("Fetching Metrics Info for node:" + node.metricId);
                node.hide = false;
                var childrenIds = JSON.parse(data.children);
                return _this._insertNewNode(node, childrenIds, all, node.childrenFetched).then(function () {
                    console.log("Inserted: " + node.chartName);
                    node.childrenFetched = true;
                    return null;
                });
            });
        }
        else {
            return null;
        }
    };
    PerformanceComponent.prototype.fetchMetricInfoById = function (node) {
        var _this = this;
        var thisNode = node;
        var p1 = { metric_id: node.metricId };
        if (node.metricId in this.cachedNodeInfo) {
            return this.cachedNodeInfo[node.metricId];
        }
        return this.apiService.post('/metrics/metric_info', p1).subscribe(function (data) {
            return data;
        }, function (error) {
            console.log(error);
            _this.componentState = "Error";
        });
    };
    PerformanceComponent.prototype.collapseNode = function (node) {
        if (node.hasOwnProperty("numChildren")) {
            // this.collapseBranch(node);
        }
        node.collapsed = true;
    };
    PerformanceComponent.prototype.collapseBranch = function (node, traversedNodes) {
        var thisIndex = this.getIndex(node);
        if (node.hasOwnProperty("numChildren")) {
            this.hideChildren(node, true);
        }
        return traversedNodes;
    };
    PerformanceComponent.prototype.hideChildren = function (node, root) {
        var totalHides = 0;
        if (!node) {
            return 0;
        }
        var thisIndex = this.getIndex(node);
        if (node.hasOwnProperty("numChildren")) {
            if (!node.childrenFetched) {
                return 0;
            }
            var nextIndex = thisIndex + 1;
            if ((nextIndex >= this.flatNodes.length) && (!node.collapsed)) {
                console.log("Huh!");
                return 0;
            }
            for (var i = 1; i <= node.numChildren && (nextIndex < this.flatNodes.length); i++) {
                var hides = 0;
                if (true) {
                    hides += this.hideChildren(this.flatNodes[nextIndex], false);
                }
                this.flatNodes[nextIndex].collapsed = true;
                this.flatNodes[nextIndex].hide = true;
                totalHides += 1 + hides;
                nextIndex += hides + 1;
            }
        }
        return totalHides;
    };
    ;
    PerformanceComponent.prototype._insertNewNode = function (node, childrenIds, all, alreadyInserted) {
        var _this = this;
        if (childrenIds.length <= 0) {
            return;
        }
        var thisNode = node;
        var thisAll = all;
        var childId = childrenIds.pop();
        var thisChildrenIds = childrenIds;
        var p1 = { metric_id: childId };
        if (!node.hasOwnProperty("childrenGuids")) {
            node.childrenGuids = [];
        }
        return this.fetchMetricInfoById({ metricId: childId }).then(function (data) {
            if (!alreadyInserted) {
                console.log("!alreadyInserted");
                return _this.getNodeFromData(data).then(function (newNode) {
                    newNode.guid = _this.guid();
                    thisNode.lineage.forEach(function (ancestor) {
                        newNode.lineage.push(ancestor);
                    });
                    newNode.lineage.push(thisNode.guid);
                    console.log("Added childGuid for node:" + node.chartName);
                    node.childrenGuids.push(newNode.guid);
                    newNode.indent = thisNode.indent + 1;
                    var index = _this.getIndex(thisNode);
                    _this.flatNodes.splice(index + 1, 0, newNode);
                    _this._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
                    newNode.hide = false;
                    if (thisAll) {
                        _this.expandNode(newNode, thisAll);
                    }
                });
            }
            else {
                console.log("alreadyInserted");
                node.childrenGuids.forEach(function (childGuid) {
                    var childNode = _this.flatNodes[_this.getIndex({ guid: childGuid })];
                    //let childrenIds = JSON.parse(data.children);
                    childNode.hide = false;
                });
                _this._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
            }
            return null;
        });
    };
    PerformanceComponent.prototype.getIndex = function (node) {
        var index = this.flatNodes.map(function (x) { return x.guid; }).indexOf(node.guid);
        return index;
    };
    PerformanceComponent.prototype.getNodeFromData = function (data) {
        var _this = this;
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
            numChildrenPassed: data.num_children_passed,
            numChildrenFailed: data.last_num_build_failed,
            lastBuildStatus: data.last_build_status,
            numLeaves: data.num_leaves,
            childrenScoreMap: {},
            status: false,
            numChildren: null
        };
        this.metricMap[newNode.metricId] = { chartName: newNode.chartName };
        if (newNode.info === "") {
            newNode.info = "<p>Please update the description</p>";
        }
        var dateRange = this.getDateRange();
        var fromDate = dateRange[0];
        var toDate = dateRange[1];
        return this.fetchScores(data.metric_id, fromDate.toISOString(), toDate.toISOString()).then(function (scoreData) {
            newNode.childrenScoreMap = scoreData["children_score_map"];
            _this.evaluateScores(newNode, scoreData["scores"]);
            newNode.childrenWeights.forEach(function (info, childId) {
                newNode.children[childId] = { weight: newNode.childrenWeights[childId], editing: false };
            });
            if (newNode.lastBuildStatus === "PASSED") {
                newNode.status = true;
            }
            else {
                newNode.status = false;
            }
            var newNodeChildrenIds = JSON.parse(data.children);
            if (newNodeChildrenIds.length > 0) {
                newNode.numChildren = newNodeChildrenIds.length;
            }
            return newNode;
        });
    };
    PerformanceComponent.prototype.fetchScores = function (metricId, fromDate, toDate) {
        var _this = this;
        var payload = {};
        payload["metric_id"] = metricId;
        payload["date_range"] = [fromDate, toDate];
        return this.apiService.post('/metrics/scores', payload).subscribe(function (data) {
            return data;
        }, function (error) {
            console.log(error);
            _this.componentState = "Error";
        });
    };
    PerformanceComponent.prototype.getDateRange = function () {
        var today = new Date();
        console.log(today);
        var startMonth = 4 - 1;
        var startDay = 1;
        var startMinute = 59;
        var startHour = 23;
        var startSecond = 1;
        var fromDate = new Date(today.getFullYear(), startMonth, startDay, startHour, startMinute, startSecond);
        fromDate = this.getDateBound(fromDate, true);
        var yesterday = this.getYesterday(today);
        var toDate = new Date(yesterday);
        toDate = this.getDateBound(toDate, false);
        return [fromDate, toDate];
    };
    PerformanceComponent.prototype.getYesterday = function (today) {
        var yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return yesterday;
    };
    PerformanceComponent.prototype.getDateBound = function (dt, lower) {
        var newDay = new Date(dt);
        if (lower) {
            newDay.setHours(0, 0, 1);
        }
        else {
            newDay.setHours(23, 59, 59);
        }
        return newDay;
    };
    PerformanceComponent.prototype.evaluateScores = function (node, scores) {
        var keys = Object.keys(scores);
        var sortedKeys = keys.sort();
        if (node.chartName === "Total") {
            this.validDates = sortedKeys;
        }
        if (Object.keys(scores).length) {
            var mostRecentDateTimestamp = sortedKeys.slice(-1)[0];
            var mostRecentDate = new Date(mostRecentDateTimestamp);
            console.log(mostRecentDate);
            console.log(scores[mostRecentDateTimestamp].score);
        }
        var goodnessValues = [];
        sortedKeys.forEach(function (key) {
            goodnessValues.push(scores[key].score);
        });
        node.goodnessValues = goodnessValues;
        try {
            node.goodness = Number(goodnessValues[goodnessValues.length - 1].toFixed(1));
        }
        catch (e) {
        }
        node.childrenGoodnessMap = {};
        node.trend = "flat";
        if (goodnessValues.length > 1) {
            var penultimateGoodness = Number(goodnessValues[goodnessValues.length - 2].toFixed(1));
            if (penultimateGoodness > node.goodness) {
                node.trend = "down";
            }
            else if (penultimateGoodness < node.goodness) {
                node.trend = "up";
            }
            if (Number(goodnessValues[goodnessValues.length - 1].toFixed(1)) === 0) {
                node.trend = "down";
            }
        }
        console.log("Node: " + node.chartName + " Goodness: " + node.goodness);
    };
    PerformanceComponent.prototype.doSomething1 = function () {
        var _this = this;
        console.log("Doing Something1");
        var payload = { "metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"] };
        this.apiService.post('/metrics/scores', payload).subscribe(function (response) {
            console.log(response.data);
            _this.componentState = response.message;
        }, function (error) {
            console.log(error);
            _this.componentState = "Error";
        });
    };
    PerformanceComponent.prototype.getComponentState = function () {
        return this.componentState;
    };
    PerformanceComponent.prototype.setValues = function (pageNumber) {
        this.data["rows"] = [['hi', 'hello'], ['how', 'are']];
        this.data["headers"] = ['Names', 'Numbers'];
        this.data["all"] = false;
        this.data["totalLength"] = 14;
        this.data["currentPageIndex"] = pageNumber;
        this.data["pageSize"] = this.data["rows"].length;
    };
    PerformanceComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-performance',
            template: __webpack_require__(/*! ./performance.component.html */ "./src/app/performance/performance.component.html"),
            styles: [__webpack_require__(/*! ./performance.component.css */ "./src/app/performance/performance.component.css")]
        }),
        __metadata("design:paramtypes", [_services_api_api_service__WEBPACK_IMPORTED_MODULE_1__["ApiService"], _services_logger_logger_service__WEBPACK_IMPORTED_MODULE_2__["LoggerService"]])
    ], PerformanceComponent);
    return PerformanceComponent;
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