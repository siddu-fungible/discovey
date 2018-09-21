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
            providers: [],
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

module.exports = "<p>\n  table works!\n</p>\n<!--<link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css\">-->\n<div class=\"card tableContainer\">\n    <div>\n        <div>\n            <!-- items being paged -->\n        <table class=\"table\" matSort (matSortChange)=\"sortData($event)\">\n          <tr>\n            <th *ngFor=\"let header of headers; index as i\" mat-sort-header=\"{{i}}\">{{ header }}</th>\n          </tr>\n          <tr *ngFor=\"let item of pagedItems\">\n            <td *ngFor=\"let rowItems of item\">{{rowItems}}</td>\n          </tr>\n        </table>\n\n            <!-- pager -->\n            <ul *ngIf=\"pager.pages && pager.pages.length\" class=\"pagination\">\n                <li [ngClass]=\"{disabled:pager.currentPage === 1}\">\n                    <a (click)=\"setPage(1)\">First</a>\n                </li>\n                <li [ngClass]=\"{disabled:pager.currentPage === 1}\">\n                    <a (click)=\"setPage(pager.currentPage - 1)\">Previous</a>\n                </li>\n                <li *ngFor=\"let page of pager.pages\" [ngClass]=\"{active:pager.currentPage === page}\">\n                    <a (click)=\"setPage(page)\">{{page}}</a>\n                </li>\n                <li [ngClass]=\"{disabled:pager.currentPage === pager.totalPages}\">\n                    <a (click)=\"setPage(pager.currentPage + 1)\">Next</a>\n                </li>\n                <li [ngClass]=\"{disabled:pager.currentPage === pager.totalPages}\">\n                    <a (click)=\"setPage(pager.totalPages)\">Last</a>\n                </li>\n            </ul>\n        </div>\n    </div>\n</div>\n"

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
/* harmony import */ var _services_pager_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../services/pager.service */ "./src/app/services/pager.service.ts");
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
    function FunTableComponent(pagerService) {
        this.pagerService = pagerService;
        // private allItems: any = [];
        this.pager = {};
        this.data = [];
        this.nextPage = new _angular_core__WEBPACK_IMPORTED_MODULE_0__["EventEmitter"]();
    }
    FunTableComponent.prototype.ngOnInit = function () {
        // console.log("Data check:" +this.data);
        this.rows = this.data["rows"];
        this.headers = this.data["headers"];
        // console.log("Allitems:" +this.allItems);
        // console.log("Allitems rows:" +this.allItems["rows"]);
        this.originalData = Array.from(this.rows);
        this.setPage(1);
    };
    FunTableComponent.prototype.setPage = function (page) {
        // get pager object from service
        if (!this.data["all"]) {
            this.nextPage.emit(page);
        }
        else {
            this.pager = this.pagerService.getPager(this.data["length"], page, 10);
            this.pagedItems = this.rows.slice(this.pager.startIndex, this.pager.endIndex + 1);
        }
    };
    FunTableComponent.prototype.paging = function (page) {
        this.pager = this.pagerService.getPager(this.data["length"], page, this.rows.length);
        this.pagedItems = this.rows.slice(0, this.rows.length);
    };
    FunTableComponent.prototype.ngOnChanges = function () {
        // this.allItems = this.data;
        // this.headers = this.data["headers"];
        // this.originalData = Array.from(this.allItems["rows"]);
        this.rows = this.data["rows"];
        this.headers = this.data["headers"];
        this.originalData = Array.from(this.rows);
        this.paging(this.data["currentPageIndex"]);
        //this.setPage(1);
    };
    FunTableComponent.prototype.sortData = function (sort) {
        if (!sort.active || sort.direction === '') {
            this.pagedItems = Array.from(this.originalData);
            this.rows = this.pagedItems;
            this.setPage(1);
            return;
        }
        this.pagedItems = this.rows.sort(function (a, b) {
            var isAsc = sort.direction === 'asc';
            if (sort.active) {
                return compare(a[sort.active], b[sort.active], isAsc);
            }
        });
        this.setPage(1);
    };
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", Object)
    ], FunTableComponent.prototype, "data", void 0);
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Output"])(),
        __metadata("design:type", _angular_core__WEBPACK_IMPORTED_MODULE_0__["EventEmitter"])
    ], FunTableComponent.prototype, "nextPage", void 0);
    FunTableComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'fun-table',
            template: __webpack_require__(/*! ./fun-table.component.html */ "./src/app/fun-table/fun-table.component.html"),
            styles: [__webpack_require__(/*! ./fun-table.component.css */ "./src/app/fun-table/fun-table.component.css")]
        }),
        __metadata("design:paramtypes", [_services_pager_service__WEBPACK_IMPORTED_MODULE_1__["PagerService"]])
    ], FunTableComponent);
    return FunTableComponent;
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
/* harmony import */ var _services_api_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../services/api.service */ "./src/app/services/api.service.ts");
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
    function PerformanceComponent(apiService) {
        this.apiService = apiService;
        this.componentState = "Unknown";
        this.data = [];
    }
    PerformanceComponent.prototype.ngOnInit = function () {
        this.data["rows"] = [['hi', 'hello'], ['how', 'are'], ['you', 'its'], ['been', 'a'], ['long', 'time'], ['also', 'when'], ['where', 'how'], ['are', 'we'], ['meeting', 'if'], ['hey', 'buddy'], ['let', 'go'], ['we', 'will']];
        this.data["headers"] = ['Names', 'Numbers'];
        this.data["all"] = true;
        this.data["length"] = 12;
        this.data["currentPageIndex"] = 1;
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
        this.data["length"] = 14;
        this.data["currentPageIndex"] = pageNumber;
    };
    PerformanceComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-performance',
            template: __webpack_require__(/*! ./performance.component.html */ "./src/app/performance/performance.component.html"),
            styles: [__webpack_require__(/*! ./performance.component.css */ "./src/app/performance/performance.component.css")]
        }),
        __metadata("design:paramtypes", [_services_api_service__WEBPACK_IMPORTED_MODULE_1__["ApiService"]])
    ], PerformanceComponent);
    return PerformanceComponent;
}());



/***/ }),

/***/ "./src/app/services/api.service.ts":
/*!*****************************************!*\
  !*** ./src/app/services/api.service.ts ***!
  \*****************************************/
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

/***/ "./src/app/services/pager.service.ts":
/*!*******************************************!*\
  !*** ./src/app/services/pager.service.ts ***!
  \*******************************************/
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