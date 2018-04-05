angular.module("analytic", [])
    .factory("analytic", function() {
        var dataService = "";

        return {
            update: function() {
            },

            setService: function(service) {
                dataService = service;
            },

            getService: function() {
                return dataService;
            }
        };
    })
    .directive("resultViewBase", ["$injector", "analytic", function($injector, analytic) {
        return {
            restrict: "E",
            templateUrl: "lib/components/analytic/resultViewBase.html",
            link: function($scope, element, attrs) {
                if (attrs.fileName !== "")
                {
                    $scope.service = $injector.get(analytic.getService());
                    $scope.service.loadFile(attrs.fileName, function(data) {
                        $scope.data = data;
                    });
                }
            }
        };
    }])
    .directive("iteratorBase", function($compile) {
        function getFileNames(obj, fileNames) {
            // Object has children, iterate through all children
            // If current has a result file process that first
            if (obj.hasOwnProperty("info") && obj.info.hasOwnProperty("resultFile") && obj.info.resultFile !== undefined && obj.info.resultFile !== '') {
                fileNames.push(obj.info.resultFile);
            }
            if (obj.hasOwnProperty("data")) {
                if (obj.data.hasOwnProperty("children")) {
                    for (var key in obj.data.children) {
                        child = obj.data.children[key];
                        getFileNames(child, fileNames);
                    }
                }
            }
            // Object doesn't have children, end of row
            else {
                if (obj.hasOwnProperty("info") && obj.info.hasOwnProperty("resultFile") && obj.info.resultFile !== undefined && obj.info.resultFile !== '') {
                    fileNames.push(obj.info.resultFile);
                }

            }
            return fileNames;
        }
        return {
            replace: true,
            restrict: 'E',
            scope: {
                data: '=data'
            },
            link: function($scope, element, attrs) {
                if ($scope.data.class !== undefined && $scope.data.class !== null) {
                    var headerFlag = true;
                    var fileNames = getFileNames($scope.data, []);
                    var htmlText = "<div load-files-dir file-name='" + fileNames + "'></div>";
                    if (htmlText !== "") {
                        $compile(htmlText)($scope, function(cloned, $scope){
                            element.append(cloned);
                        });
                    }
                }
            }
        };
    })
    .directive('loadFilesDir', function() {
        return {
            scope: {
                'fileName': '@'
            },
            controller: ["$scope", "$injector", "analytic", function($scope, $injector, analytic) {
                if ($scope.fileName !== "")
                {
                    var fileArray = $scope.fileName.split(',');
                    $scope.service = $injector.get(analytic.getService());
                    $scope.dataObject = [];
                    for (var key in fileArray) {
                        file = fileArray[key];
                        $scope.service.loadFile(file, function(data) {
                            $scope.dataObject.push(data);
                        });
                    }
                }
            }],
            template: '<div iterator-table-dir file-data={{dataObject}}></div>'
        };
    })
    .directive('iteratorTableDir', function ($compile) {
        var getInfoHeader = function(info, iterInfo) {
            var dataHeader = {"columnNames": [],
                          "row": []};
            // Get current file
            dataHeader.columnNames.push("");
            dataHeader.row.push(info.resultFile);

            for (var index in info.parent_iteration_info) {
                var item = info.parent_iteration_info[index];
                var header = item.param;
                var value = item.value;
                dataHeader.columnNames.push(header);
                dataHeader.row.push(value);
            }

            // Get current info
            var header = info.param;
            var value = info.value;
            dataHeader.columnNames.push(header);
            dataHeader.row.push(value);

            return dataHeader;
        };

        var parseIterFiles = function(obj, header, loopKey) {
            var dataArray = [];
            if (obj.hasOwnProperty("class") && obj.class == "tableDbQuery") {
                var iterObj = {
                    "info": {
                        "displayName": ""
                    },
                    "data": {
                        "columnNames": [],
                        "rows": []
                    }
                };
                // Copy parent header columns
                iterObj.data.columnNames = header.columnNames;

                // Copy Iteration Data
                if (obj.hasOwnProperty("data") && obj.data.hasOwnProperty("rows")) {
                    // Copy Table title
                    iterObj.info.displayName = obj.info.displayName;

                    // Copy data header columns - only
                    iterObj.data.columnNames = iterObj.data.columnNames.concat(obj.data.columnNames);

                    for (var rIdx in obj.data.rows) {
                        // Copy header row values
                        var row = header.row;
                        row = row.concat(obj.data.rows[rIdx]);

                        // Add row to iterObj
                        iterObj.data.rows.push(row);
                    }
                }
                dataArray.push(iterObj);
            }
            if (obj.hasOwnProperty("data") && obj.data.hasOwnProperty("children")){
                for (var key in obj.data.children) {
                    var child = obj.data.children[key];
                    var recurse = parseIterFiles(child, header, loopKey);
                    angular.extend(dataArray, recurse);
                }
            }
            return dataArray;
        };

        var buildTables = function(iterationData) {
            var dataArray = [];
            for (var key in iterationData) {
                var obj = iterationData[key];

                // Get header info that applies to all tables in obj
                var header = getInfoHeader(obj.info);

                // Get array of all tables in obj with applied header info
                var iterArr = parseIterFiles(obj, header, key);

                dataArray = dataArray.concat(iterArr);
            }
            return dataArray;
        };

        return {
            require: '^loadFilesDir',
            scope: {
                'fileData': '@'
            },
            link: function(scope, element, attrs) {
                attrs.$observe('fileData', function(iterationData) {
                    var allTables = [];
                    allTables = buildTables(angular.fromJson(iterationData));
                    scope.dataArray = allTables;
                });
            },
            templateUrl: 'lib/components/analytic/iterationTable.html'
        };
    })

    // Not used: recursion handled in html, template called directly
    // .directive("drilldown", function($compile) {
        // return {
            // templateUrl: 'lib/components/analytic/drvDrilldownBase.html',
            // restrict: 'E',
            // replace: true,
            // scope: {
                // data: '=data'
            // },
            // link: function(scope, element, attrs) {
                // htmlText = "<drilldown data='data.drillDownResults'/>"
                // if (scope.data.hasOwnProperty("drillDownResults")) {
                    // $compile(htmlText)(scope, function(cloned, scope){
                        // element.append(cloned);
                    // });
                // }
            // }
        // };
    // })
    .directive('chart', function () {
        return {
            restrict: 'E',
            replace: true,
            template: '<div></div>',
            scope: {
                config: '='
            },
            link: function (scope, element, attrs) {
                var chart;
                var process = function () {
                    var defaultOptions = {
                        chart: { renderTo: element[0] },
                    };
                    var config = angular.extend(defaultOptions, scope.config);
                    chart = new Highcharts.Chart(config);
                };
                process();
                scope.$watch("config.series", function (loading) {
                    process();
                });
                scope.$watch("config.loading", function (loading) {
                    if (!chart) {
                        return;
                    }
                    if (loading) {
                        chart.showLoading();
                    } else {
                        chart.hideLoading();
                    }
                });
            }
        };
    })
    .controller("resultCtrl", ["$scope", "$injector", "analytic", "$location", "$anchorScroll", function($scope, $injector, analytic, $location, $anchorScroll) {
        $scope.openInTab = function(file) {
            window.open("http://localhost:8000/testResult.html?fileName=" + file,'_blank');
        };

        $scope.scrollTo = function(id) {
            $location.hash(id);
            $anchorScroll();
        };

        $scope.capFirstLetter = function(string) {
            retStr = string;
            if (retStr !== undefined) {
                retStr = string.charAt(0).toUpperCase() + string.slice(1);
            }
            return retStr;
        };

        $scope.grade = function(value) {
            val = String(value).trim().toUpperCase();
            switch(val) {
                case "FAILED":
                    return {'grade':'F', 'grade-desc':'class grade-desc-f', 'grade-bg':'class grade-cont grade-bg-f'};
                case "PASSED":
                    return {'grade':'P', 'grade-desc':'class grade-desc-a', 'grade-bg':'class grade-cont grade-bg-a'};
                default:
                    return {'grade':'I', 'grade-desc':'class grade-desc-i', 'grade-bg':'class grade-cont grade-bg-i'};
            }
        };

        $scope.verdictLabel = function(value) {
            val = String(value).trim().toUpperCase();
            switch(val) {
                case "FAILED":
                    return "btn-danger";
                case "PASSED":
                    return "btn-success";
                case "NONE":
                    return "btn-info";
                default:
                    return "btn-warning";
            }
        };

        $scope.verdictFormat = function(value) {
            if (value !== undefined)
                return value.charAt(0).toUpperCase() + value.slice(1);
        };

        $scope.showResult = function(data, shStat) {
            if (data.hasOwnProperty("info") && data.info.hasOwnProperty("reportGroup") && data.info.reportGroup === "SUMMARY") {
                return true;
            }
            else {
                return shStat;
            }
        };

        $scope.hasResultFile = function(obj) {
            var hasFile = false;
            if (obj.hasOwnProperty("info") && obj.info.hasOwnProperty("resultFile") && obj.info.resultFile !== "") {
                hasFile = true;
            }
            if (obj.hasOwnProperty("data") && obj.data.hasOwnProperty("children")) {
                // Object has children, iterate through all children
                for (var key in obj.data.children) {
                    child = obj.data.children[key];
                    if ($scope.hasResultFile(child)) {
                        hasFile = true;
                    }
                }
            }
            return hasFile;
        };

        $scope.hasMoreDetail = function(data) {
            if (data.result_file)
            {
                return true;
            }
            else
            {
                return false;
            }
        };

        function forEach (obj, callback) {
            if (obj === undefined) {
                console.log ("===FOR EACH UNDEFINED===" + obj);
                return obj;
            }

            var i = 0,
                length = obj.length,
                isArray = Array.isArray(obj);

            if (isArray) {
                for (; i < length; i++) {
                    if (callback.call(obj[i], i, obj[i]) === false) {
                        break;
                    }
                }
            } else {
                for (i in obj) {
                    if (callback.call(obj[i], i, obj[i]) === false) {
                        break;
                    }
                }
            }
            return obj;
        }

        function mergeDeep (o1, o2) {
            if (o1 === undefined)
                return o2;

            //console.log ("++MD: " + JSON.stringify(o1) + " ++ " + JSON.stringify(o2))
            var tempNewObj = o1;

            //if o1 is an object - {}
            if (o1.length === undefined && typeof o1 !== "number") {
                //console.log ("OBJECT")
                forEach(o2, function(key, value) {
                    if (o1[key] === undefined) {
                        tempNewObj[key] = value;
                    } else {
                        tempNewObj[key] = mergeDeep(o1[key], o2[key]);
                    }
                });
            }

            //else if o1 is an array - []
            else if (o1.length > 0 && typeof o1 !== "string") {
                //console.log ("ARRAY")
                forEach(o2, function(index) {
                    tempNewObj[index] = mergeDeep(o1[index], o2[index]);
                });
            }

            //handling other types like string or number
            else {
                //taking value from the second object o2
                //could be modified to keep o1 value with tempNewObj = o1;
                tempNewObj = o2;
            }
            //console.log("++++RET: " + JSON.stringify(tempNewObj))
            return tempNewObj;
        }

        $scope.configChart = function(chartConfig) {
            return chartConfig;
        };
    }])
    .controller("toggle", ["$scope", function($scope) {
        $scope.drill = false;
        $scope.$watch('drill', function(){
            $scope.drillText = $scope.drill ? '-' : '+';
        });
    }])
    .controller("toggleView", ["$scope", function($scope) {
        $scope.docView = false;
        $scope.viewText = "Show";
        $scope.$watch('docView', function(){
            $scope.viewText = $scope.docView ? "Hide" : "Show";
        });
    }]);
