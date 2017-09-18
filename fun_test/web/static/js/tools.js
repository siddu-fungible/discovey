currentWorkFlow = "demo";
var charts = [];

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


$("#workflow-start-button").click(function(){
  selectedF1s = [];
  selectedWorkFlow = currentWorkFlow;
  $("#f1-table-tbody > tr").each(function() {
      //console.log("Hie2");
      $(this).filter(":has(:checkbox:checked)").find("input").each(function() {
        selectedF1Ip = $(this).attr("data-f1-ip");
        selectedF1s.push(selectedF1Ip);
        console.log(selectedWorkFlow);
      });
  });
  $.map(selectedF1s, function(selectedF1){
    console.log(selectedF1);
    $("#f1-table-tbody > tr").each(function() {
      $(this).find(".progress-bar").each(function() {

        if($(this).attr("data-f1-ip") === selectedF1) {
          progressBar = $(this);
          var step_count = 0;
          (function(progressBar) {
            workFlowStart(selectedF1);
            $.ajax({
              url: "/tools/f1/workflow/" + selectedWorkFlow,
              type: 'get',
              dataType: 'json',
              success: function(data) {
                stepCount = data.length;
                doStuff(0, stepCount);
                function doStuff(stepIndex, stepCount) {
                    payload = {"f1_ip": selectedF1, "workflow": selectedWorkFlow, "step-index": stepIndex};
                    (function(selectedF1, stepIndex, progressBar, stepCount) {

                      $.ajax({
                        url: "/tools/f1/start_workflow_step",
                                dataType: 'text',
                                type: 'post',
                                contentType: 'application/json',
                                async: true,
                                data: JSON.stringify(payload),
                                success: function(data) {
                                  console.log("IP:" + selectedF1);
                                  width = ((stepIndex + 1) /stepCount) * 100;
                                  $(progressBar).css("width", width.toString() + "%");
                                  if((stepIndex + 1) < stepCount) {
                                    doStuff(stepIndex + 1, stepCount);
                                  } else {
                                    workFlowComplete(selectedF1);
                                  }
                                },
                                error: function(data) {
                                    alert("Huh2?");
                                }
                          });
                    }(selectedF1, stepIndex, progressBar, stepCount));
                };
              },
              error: function(data) {
                alert("Whaaaa?");
              }
            });
          }(progressBar));


        }
      });
    });

  });
});



(function() {
  var app;

  app = angular.module('tools', []);

  app.controller('AppController', [
    '$scope', '$http', '$window', function($scope, $http, $window) {
      $scope.currentWorkFlow = null;
      $scope.steps = [];
      $scope.workFlowClick = function(event) {
        //alert(event.target.id);
        workFlowName = event.target.id;
        $scope.currentWorkFlow = event.target.innerText;
        $window.currentWorkFlow = $scope.currentWorkFlow;
        //alert(event.target.innerText);
        $http.get('/tools/f1/workflow/' + workFlowName).then(function(result){
          $scope.steps = result.data;
        });
      };

      $scope.replaceIpDot = function(Ip) {
        return Ip.replace(new RegExp("\\.", 'g'), "_");
      }


      $scope.posts = [];
      $scope.f1s = [];
      $scope.workflows = [];
      $scope.traffic_generators = [];
      $http.get('/tools/f1').then(function(result){
        angular.forEach(result.data, function(f1){
          //console.log(f1["name"]);
          $scope.f1s.push(f1);
        });
      });

      $http.get('/tools/f1/workflows').then(function(result) {
        $scope.workflows = result.data;
      });

      $http.get('/tools/tg').then(function(result) {
        $scope.traffic_generators = result.data;
      });

      return $scope;
    }

  ]);

}).call(this);

function Chart(divName) {
    let trace1 = {
      x: [],
      y: [],
      type: 'scatter'
    };
    let trace2 = {
      x: [],
      y: [],
      type: 'scatter'
    };
    this.divName = divName;
    Plotly.newPlot(this.divName, [trace1, trace2]);
    this.xValue = 0;

}

Chart.prototype.updatePlot = function() {
    var that = this;
    setTimeout(
    function()
    {
      //console.log("Hi");
      that.xValue = that.xValue + 1;
      that.y1Value = randomNumberFromRange(0, 10);
      that.y2Value = randomNumberFromRange(0, 10);
      //console.log(that.divName + " " + that.y1Value + " " + that.y2Value);

      Plotly.extendTraces(that.divName,
        {x: [[that.xValue], [that.xValue]],
         y: [[that.y1Value], [that.y2Value]]}, [0, 1]);
      that.updatePlot();
    }, 2000);

}


function randomNumberFromRange(min, max)
{
  return Math.floor(Math.random()* (max-min + 1) + min);
}

function plotIt() {
  let ch1 = new Chart('chart1-div');
  ch1.updatePlot();

  let ch2 = new Chart('chart2-div');
  ch2.updatePlot();

  let ch3 = new Chart('chart3-div');
  ch3.updatePlot();

  let ch4 = new Chart('chart4-div');
  ch4.updatePlot();

}



$("#start-traffic-button").click(function () {
  plotIt();
});
$(document).ready(function() {
  plotIt();
});
