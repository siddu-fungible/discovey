currentWorkFlow = "demo";
let charts = [];
let statsOn = false;

function workFlowComplete(f1Ip) {
    replacedIp = f1Ip.replace(new RegExp("\\.", 'g'), "_");
    $("#workflow-progress-label-" + replacedIp).hide();
    $("#workflow-progress-div-" + replacedIp).hide();
    icon = "#workflow-progress-icon-" + replacedIp;
    $(icon).show();
    $(icon).removeClass("glyphicon-hourglass");
    $(icon).addClass("glyphicon-ok");
}

function workFlowStart(f1Ip) {
    replacedIp = f1Ip.replace(new RegExp("\\.", 'g'), "_");
    $("#workflow-progress-label-" + replacedIp).hide();
    $("#workflow-progress-div-" + replacedIp).show();
    icon = $("#workflow-progress-icon-" + replacedIp);
    $(icon).hide();
    $("#workflow-progress-bar-" + replacedIp).css("width", "0%");
}


$("#workflow-start-button").click(function () {
    selectedF1s = [];
    //selectedWorkFlow = currentWorkFlow;
    $("#f1-table-tbody > tr").each(function () {
        //console.log("Hie2");
        $(this).filter(":has(:checkbox:checked)").find("input").each(function () {
            selectedF1Ip = $(this).attr("data-f1-ip");
            selectedF1s.push(selectedF1Ip);
            //console.log(selectedWorkFlow);
        });
    });
    $.map(selectedF1s, function (selectedF1) {
        console.log(selectedF1);
        $("#f1-table-tbody > tr").each(function () {
            $(this).find(".progress-bar").each(function () {

                if ($(this).attr("data-f1-ip") === selectedF1) {
                    progressBar = $(this);
                    (function (progressBar) {
                        workFlowStart(selectedF1);
                        $.ajax({
                            url: "/tools/f1/workflow/" + selectedWorkFlow,
                            type: 'get',
                            dataType: 'json',
                            success: function (data) {
                                stepCount = data.length;
                                doStuff(0, stepCount);

                                function doStuff(stepIndex, stepCount) {
                                    payload = {
                                        "f1_ip": selectedF1,
                                        "workflow": selectedWorkFlow,
                                        "step-index": stepIndex
                                    };
                                    (function (selectedF1, stepIndex, progressBar, stepCount) {

                                        $.ajax({
                                            url: "/tools/f1/start_workflow_step",
                                            dataType: 'text',
                                            type: 'post',
                                            contentType: 'application/json',
                                            async: true,
                                            data: JSON.stringify(payload),
                                            success: function (data) {
                                                console.log("IP:" + selectedF1);
                                                width = ((stepIndex + 1) / stepCount) * 100;
                                                $(progressBar).css("width", width.toString() + "%");
                                                if ((stepIndex + 1) < stepCount) {
                                                    doStuff(stepIndex + 1, stepCount);
                                                } else {
                                                    workFlowComplete(selectedF1);
                                                }
                                            },
                                            error: function (data) {
                                                alert("Huh2?");
                                            }
                                        });
                                    }(selectedF1, stepIndex, progressBar, stepCount));
                                }
                            },
                            error: function (data) {
                                alert("Whaaaa?" + data.toString());
                            }
                        });
                    }(progressBar));


                }
            });
        });

    });
});


(function () {
    let app;
    app = angular.module('tools', []);



    app.controller('AppController', [
        '$scope', '$http', '$window', '$timeout', function ($scope, $http, $window, $timeout) {
            pollInterval = 2000; // seconds
            $scope.currentWorkFlow = null;
            $scope.steps = [];
            $scope.topologySessionId = null;
            $scope.deployButtonText = "Deploy";
            //$scope.selectedWorkFlow = null;
            $scope.commonWorkFlow = null;

            $scope.createVolumeInfo = {
                "name": "default_name",
                "uuid": "default_uuid",
                "blockSize": 1024,
                "nsId": 64,
                "size": 1024
            };

            $scope.workFlowClick = function (event) {
                //alert(event.target.id);
                workFlowName = event.target.id;
                $scope.currentWorkFlow = event.target.innerText;
                $window.currentWorkFlow = $scope.currentWorkFlow;
                //alert(event.target.innerText);
                $http.get('/tools/f1/workflow/' + workFlowName).then(function (result) {
                    $scope.steps = result.data;
                });
            };

            $scope.workFlowSelection = function (selectedWorkFlow) {
                $scope.commonWorkFlow = selectedWorkFlow["id"];
            };

            $scope.replaceIpDot = function (Ip) {
                return Ip.replace(new RegExp("\\.", 'g'), "_");
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
                        });
                        $scope.deployButtonText = "Deploy";
                    }
                }).catch(function (result) {
                    //alert("Topology status check failed");
                });
            };

            $scope.deployTopologyClick = function (event) {
                $http.get('/tools/topology').then(function (result) {
                    let sessionId = result.data["session_id"];
                    $scope.topologySessionId = sessionId;
                    $scope.deployButtonText = "Deploying";
                    //console.log(sessionId);
                    $timeout(function () {
                        getTopologyStatus(sessionId)
                    }, pollInterval);

                });

            };

            $scope.testClick = function (event) {
              console.log("TestClick");
              console.log($scope.createVolumeInfo);
            };

            $scope.posts = [];
            $scope.f1s = [];
            $scope.workflows = [];
            $scope.traffic_generators = [];


            $http.get('/tools/f1/workflows').then(function (result) {
                $scope.workflows = result.data;
            });

            $http.get('/tools/tg').then(function (result) {
                $scope.traffic_generators = result.data;
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
    initPlots();
    //startPlots();
});


