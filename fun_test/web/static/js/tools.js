currentWorkFlow = "demo";
let charts = [];
let statsOn = false;

    var router = new Image();
    var f1 = new Image();
    router.src = 'http://etherealmind.com/wp-content/uploads/2010/01/cisco-router-icon.jpg';
    f1.src = 'http://icons.iconarchive.com/icons/hydrattz/multipurpose-alphabet/48/Letter-F-black-icon.png';


function draw() {



  var ctx = document.getElementById('topology-canvas').getContext('2d');

  ctx.globalCompositeOperation = 'destination-over';
  ctx.clearRect(0, 0, 2000, 2000); // clear canvas


  ctx.drawImage(router, 300, 0, 100, 100);
  ctx.drawImage(router, 600, 0, 100, 100);
  ctx.drawImage(router, 900, 0, 100, 100);


  ctx.drawImage(f1, 0, 200, 100, 100);
  ctx.drawImage(f1, 250, 200, 100, 100);
  ctx.drawImage(f1, 500, 200, 100, 100);
  ctx.drawImage(f1, 750, 200, 100, 100);
  ctx.drawImage(f1, 1000, 200, 100, 100);

  /*
  ctx.beginPath();
  ctx.moveTo(0, 200);
  ctx.lineTo(300, 0);
  ctx.stroke();*/
  //ctx.drawLine();

  window.requestAnimationFrame(draw);

}



(function () {
    let app;
    app = angular.module('tools', []);



    app.controller('AppController', [
        '$scope', '$http', '$window', '$timeout', function ($scope, $http, $window, $timeout) {
            pollInterval = 2000; // seconds
            $scope.steps = [];
            $scope.topologySessionId = null;
            $scope.deployButtonText = "Deploy";
            $scope.commonWorkFlow = null;
            $scope.commonTrafficWorkFlow = null;
            $scope.f1s = [];
            $scope.workFlows = [];
            $scope.trafficWorkFlows = [];
            $scope.currentF1 = null;
            $scope.currentWorkFlowF1 = null;

            $scope.createVolumeInfo = {
                "name": "default_name",
                "uuid": "default_uuid",
                "blockSize": 1024,
                "nsId": 64,
                "size": 1024
            };

            $scope.$onInit = function () {
                // TODO $scope.deployTopologyClick();
            };

            $scope.attachTgInfo = {

            };

            $scope.setCommonWorkFlow = function (selectedWorkFlow, f1) {
                //console.log("Parent workflow selection");
                $scope.commonWorkFlow = selectedWorkFlow;
                $scope.currentWorkFlowF1 = f1;
            };

            $scope.setCommonTrafficWorkFlow = function (selectedWorkFlow, f1) {
                $scope.commonTrafficWorkFlow = selectedWorkFlow;
                console.log("Parent workflow selection:" + $scope.commonTrafficWorkFlow);
                $scope.currentWorkFlowF1 = f1;
            };

            $scope.toggleF1Selection = function(f1){
                f1.isRowSelected = !f1.isRowSelected;
            };

            $scope.setActiveTab = function (tabName, f1) {
                console.log("Setting active tab");
                angular.element(document.querySelector('#' + tabName + "-nav-link")).tab('show');
                //angular.element(document.querySelector('#[href="#' + tabName + '-container"]')).tab('show');
                $scope.currentF1 = f1;
            };

            $scope.getSelectedF1s = function () {
                selectedF1s = [];
                for(let i = 0; i < $scope.f1s.length; i++){
                    if($scope.f1s[i].isRowSelected === true){
                        selectedF1s.push($scope.f1s[i]);
                    }
                }
                return selectedF1s;
            };

            $scope.replaceIpDot = function (iP) {
                return iP.replace(new RegExp("\\.", 'g'), "_");
            };

            let getTopologyStatus = function (sessionId) {
                $http.get("/tools/topology/status/" + sessionId.toString()).then(function (result) {
                    status = result.data["status"];
                    if ((status === "NOT_RUN") || (status === "IN_PROGRESS")) {
                        $timeout(function () {
                            getTopologyStatus(sessionId)
                        }, pollInterval);
                    } else {
                        $http.get('/tools/f1/' + $scope.topologySessionId).then(function (result) {
                            angular.forEach(result.data, function (f1) {
                                //console.log(f1["name"]);
                                $scope.f1s.push(f1);
                            });
                            // TODO:
                            //$scope.setActiveTab("details", $scope.f1s[0]);  // Test purposes only
                        });
                        $scope.deployButtonText = "Deploy";


                    }
                }).catch(function (result) {
                    //alert("Topology status check failed");
                });
            };

            $scope.deployTopologyClick = function () {
                $http.get('/tools/topology').then(function (result) {
                    let sessionId = result.data["session_id"];
                    $scope.topologySessionId = sessionId;
                    console.log("Topology session id:" + $scope.topologySessionId);
                    $scope.deployButtonText = "Deploying";
                    //console.log(sessionId);
                    $timeout(function () {
                        getTopologyStatus(sessionId)
                    }, pollInterval);

                });

            };

            $scope.cleanupTopologyClick = function () {
                $http.get('/tools/topology/cleanup').then(function (result) {
                });
            };
            $scope.testClick = function (event) {
              console.log("TestClick");
              console.log($scope.commonWorkFlow);
            };

            $http.get('/tools/f1/workflows').then(function (result) {
                $scope.workFlows = result.data;
            });

            $http.get('/tools/f1/traffic_workflows').then(function (result) {
                $scope.trafficWorkFlows = result.data;
            });

            return $scope;
        }

    ]);

}).call();

function Chart(divName, f1s, title) {
    this.f1s = f1s;
    this.title = title;
    this.statsOn = false;
    this.traceCount = this.f1s.length;
    let layout = {
        title: title,
        xaxis: {
            title: 'Sample',
            titlefont: {
                family: 'Courier New, monospace',
                size: 18,
                color: '#7f7f7f'
            }
        },
        yaxis: {
            title: title,
            titlefont: {
                family: 'Courier New, monospace',
                size: 18,
                color: '#7f7f7f'
            }
        }
    };
    this.divName = divName;
    let data = [];
    for (let i = 0; i < this.traceCount; i++) {
        data.push({
            x: [],
            y: [],
            type: 'scatter',
            name: f1s[i]

        });
    }
    Plotly.newPlot(this.divName, data, layout);
    this.xValue = 0;

}

Chart.prototype.updatePlot = function () {
    if (!this.statsOn) {
        return;
    }
    let that = this;
    setTimeout(
        function () {
            that.xValue = that.xValue + 1;


            that.xValueList = [];
            that.yValueList = [];
            that.traceList = [];
            for (let i = 0; i < that.traceCount; i++) {
                that.xValueList.push([that.xValue]);
                f1Id = that.f1s[i];

                $.ajax({
                    url: "/tools/f1/" + f1Id + "/" + that.title,
                    dataType: 'json',
                    type: 'get',
                    contentType: 'application/json',
                    async: true,
                    context: that,
                    success: function (data) {
                        yValue = parseInt(data["value"]);
                        //console.log("Value:" + yValue);
                        that.yValueList.push([parseInt(data["value"])]);
                        if (that.yValueList.length === that.traceCount) {
                            Plotly.extendTraces(that.divName,
                                {
                                    x: this.xValueList,
                                    y: this.yValueList
                                }, this.traceList);
                            that.updatePlot();
                        }

                    },
                    error: function (data) {
                        //alert("Huh3?");
                    }
                });


                that.traceList.push(i);
            }
        }
        , 2000);
};


function randomNumberFromRange(min, max) {
    return Math.floor(Math.random() * (max - min + 1) + min);
}

function startPlots() {
    for (let i = 0; i < charts.length; i++) {
        charts[i].updatePlot();
    }
}

function initPlots() {
    f1s = [];
    f1s.push("f1");
    f1s.push("f2");
    f1s.push("f3");

    let ch1 = new Chart('chart1-div', f1s, "Read/s");
    charts.push(ch1);

    let ch2 = new Chart('chart2-div', f1s, "Writes/s");
    charts.push(ch2);

    let ch3 = new Chart('chart3-div', f1s, "X/s");
    charts.push(ch3);

    let ch4 = new Chart('chart4-div', f1s, "Y/s");
    charts.push(ch4);
}


$("#stats-play-button").click(function () {
    statsOn = false;
    let playIcon = $("#stats-play-icon");
    let playButton = $("#stats-play-button");
    if (playIcon.hasClass("glyphicon-play")) {
        playIcon.removeClass("glyphicon-play");
        playIcon.addClass("glyphicon-pause");
        let icon = playButton.find("i");
        playButton.text("");
        playButton.append($(icon));
        playButton.append("Pause");


        statsOn = true;
    } else {
        playIcon.removeClass("glyphicon-pause");
        playIcon.addClass("glyphicon-play");
        let icon = playButton.find("i");
        playButton.text("");
        playButton.append($(icon));
        playButton.append("Resume");
        statsOn = false;
    }
    for (let i = 0; i < charts.length; i++) {
        charts[i].statsOn = statsOn;
    }
    if (statsOn) {
        startPlots();
    }
});


$(document).ready(function () {
    //initPlots();
    //startPlots();
    window.requestAnimationFrame(draw);

});


