angular.module("methResult", ["analytic", "ngResource"])
    .run(["analytic" , function(analytic) {
        analytic.setService("stcJsonReader");
    }])
    .factory("stcJsonReader", ["$resource", function($resource) {
        var svc = {};
        svc.loadFile = function(url, func){
            if (url === "" || url === undefined)
                url = "testReport.json"
            path = "lib/js/" + url
            console.log("Trying to read file " + path)
            $resource(path).get(func)
        }
        return svc;
    }]);
