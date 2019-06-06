import {Component, OnInit, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {Title} from "@angular/platform-browser";
import {CommonService} from "../services/common/common.service";
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})

export class AdminComponent implements OnInit {
  status: string = null;
  metricsList: any[] = [];
  modules: any;
  modelsInfo: any;
  selectedModule: any = null;
  previewDataSets: any;

  constructor(
    private apiService: ApiService,
    private loggerService: LoggerService,
    private title: Title,
    private commonService: CommonService,
    private activatedRoute: ActivatedRoute,
    private router: Router
  ) {
  }

  ngOnInit() {
    console.log("Component Init");
    this.title.setTitle('Admin');
    this.status = "Loading";
    this.metricsList = [];
    this.fetchModules();
    this.modelsInfo = {};
    this.status = null;
  }

  fetchModules(): void {
    this.apiService.get("/regression/modules").subscribe(response => {
            this.modules = response.data;
            this.modules.forEach((module) => {
                let moduleName = module.name;
            })
        }, error => {
      this.loggerService.error("fetchModules");
    })
  }

  addChartClick(): void {

  }

  editChartClick(): void {
    
  }
  
  showScores(metricId): void {
    let url = "/metrics/score_table/" + metricId;
    window.open(url, '_blank');
  }

  moduleChange(): void {
    let payload = {};
    let thisModule = this.selectedModule;
        if (this.selectedModule) {
            payload["module_name"] = this.selectedModule;
            this.apiService.post("/metrics/models_by_module", payload).subscribe((models) => {
                this.modelsInfo[thisModule] = models.data;
            }, error => {
              this.loggerService.error("moduleChange")
            })
        }
  }

  removeClick(index): void {
            this.previewDataSets.splice(index, 1);
        };

}

// function MetricsController($scope, $http, $window, commonService, $timeout, $modal) {
//
//     $scope.moduleChange = () => {
//         console.log($scope.selectedModule);
//         let payload = {};
//         let thisModule = $scope.selectedModule;
//         if ($scope.selectedModule) {
//             payload["module_name"] = $scope.selectedModule;
//             commonService.apiPost("/metrics/models_by_module", payload, "moduleChange").then((models) => {
//                 $scope.modelsInfo[thisModule] = models;
//             })
//         }
//
//     };
//
//     $scope.addChartClick = (modelName) => {
//         $modal.open({
//             templateUrl: "/static/qa_dashboard/edit_chart.html",
//             controller: ['$modalInstance', '$scope', 'commonService', '$http', 'metricId', 'chartName', 'internalChartName', 'modelName', EditChartController],
//             resolve: {
//                 chartName: () => {
//                     return null;
//                 },
//                 internalChartName: () => {
//                     return null;
//                 },
//                 modelName: () => {
//                     return modelName;
//                 },
//                 metricId: () => {
//                     return null;
//                 }
//             }
//         }).result.then(function () {
//         }).catch(function () {
//         });
//     };
//
//     $scope.editChartClick = (chartInfo, modelName) => {
//         $modal.open({
//             templateUrl: "/static/qa_dashboard/edit_chart.html",
//             controller: ['$modalInstance', '$scope', 'commonService', '$http', 'metricId', 'chartName', 'internalChartName', 'modelName', EditChartController],
//             resolve: {
//                 chartName: () => {
//                     return chartInfo.chart_name;
//                 },
//                 modelName: () => {
//                     return modelName;
//                 },
//                 internalChartName: () => {
//                     return chartInfo.internal_chart_name;
//                 },
//                 metricId: () => {
//                     return chartInfo.metric_id;
//                 }
//             }
//         }).result.then(function () {
//         }).catch(function () {
//         });
//     };
//
//     $scope.showScores = (metricId) => {
//         let url = "/metrics/score_table/" + metricId;
//         $window.open(url, '_blank');
//     };

//     function EditChartController($modalInstance, $scope, commonService, $http, metricId, chartName, internalChartName, modelName) {
//         let ctrl = this;
//         $scope.mode = "Edit";
//         if(!chartName) {
//             $scope.mode = "Create";
//         }
//         $scope.chartName = chartName;
//         $scope.internalChartName = internalChartName;
//         $scope.y1AxisTitle = null;
//         $scope.y2AxisTitle = null;
//         $scope.modelName = modelName;
//         $scope.chartInfo = null;
//         $scope.copyChartInfo = null;
//         $scope.previewDataSets = [];
//         $scope.addDataSet = null;
//         $scope.outputList = [];
//         $scope.tableInfo = null;
//         $scope.dummyChartInfo = {"output": {"min": 0, "max": -1}};
//         $scope.showOutputSelection = true;
//         $scope.negativeGradient = null;
//         $scope.metricId = metricId;
//         $scope.owner = "Unknown";
//         $scope.source = "Unknown";
//
//
//         let payload = {};
//         //payload["metric_model_name"] = modelName;
//         //payload["chart_name"] = chartName;
//         payload["metric_id"] = metricId;
//
//         $scope.describeTable = () => {
//             $scope.inputs = [];
//             payload["editing_chart"] = true;
//             commonService.apiPost("/metrics/describe_table/" + modelName, payload, "fetchMetricsData").then(function (tableInfo) {
//                 $scope.tableInfo = tableInfo;
//                 angular.forEach($scope.tableInfo, (fieldInfo, field) => {
//                     let oneField = {};
//                     oneField.name = field;
//                     if('choices' in fieldInfo && oneField.name.startsWith("input")) {
//                         oneField.choices = fieldInfo.choices.map((choice)=> { return choice[1]});
//                         $scope.inputs.push(oneField);
//                     }
//                     if(oneField.name.startsWith("output")) {
//                         $scope.outputList.push(oneField.name);
//                     }
//                 });
//             });
//         };
//
//         $scope.outputChange = () => {
//             if($scope.selectedOutput) {
//                 $scope.dummyChartInfo.output.name = $scope.selectedOutput;
//             }
//         };
//
//
//         $scope.describeTable();
//
//         // Fetch chart info
//
//
//         if($scope.chartName) {
//             commonService.apiPost("/metrics/chart_info", payload, "EditChartController: chart_info").then((chartInfo) => {
//                 $scope.chartInfo = chartInfo;
//                 //$scope.copyChartInfo = angular.copy($scope.chartInfo);
//                 $scope.previewDataSets = $scope.chartInfo.data_sets;
//                 $scope.negativeGradient = !$scope.chartInfo.positive;
//                 $scope.owner = $scope.chartInfo.owner_info;
//                 $scope.source = $scope.chartInfo.source;
//                 $scope.baseLineDate = $scope.chartInfo.base_line_date;
//
//             });
//         } else {
//         }
//
//
//         $scope.addDataSetClick = () => {
//             $scope.addDataSet = true;
//             //let newDataSet = {};
//
//             if(!$scope.tableInfo) {
//                 return $scope.describeTable();
//             }
//             $scope.addDataSet = {};
//
//
//
//             $scope.addDataSet["inputs"] = $scope.inputs;
//             $scope.addDataSet["output"] = {min: 0, max: -1};
//             /*
//             let outputName = "";
//             if($scope.previewDataSets.length > 0) {
//                 let firstChartInfoDataSet = $scope.previewDataSets.data_sets[0];
//                 outputName = firstChartInfoDataSet.output.name;
//                 $scope.selectedOutput = outputName;
//             } else {
//                 outputName = $scope.selectedOutput;
//             }
//
//             $scope.addDataSet["output"] = {"name": $scope.selectedOutput, "min": 0, "max": 99999};
//             */
//             /*newDataSet["inputs"] = {};
//             $scope.addDataSet["inputs"].forEach((oneField) => {
//                 newDataSet["inputs"][oneField.name] = oneField.selectedChoice;
//             })*/
//
//         };
//
//         $scope.addClick = () => {
//             $scope.showOutputSelection = false;
//             let error = false;
//             //
//             let validDataSet = {};
//             validDataSet["inputs"] = {};
//             validDataSet["output"] = {};
//             if($scope.addDataSet) {
//
//                 // lets validate all inputs
//                 $scope.addDataSet["inputs"].forEach((oneField) => {
//                     if(!oneField.selectedChoice && oneField.name !== "input_date_time" && oneField.choices.length) {
//                         let message = "Please select a choice for " + oneField.name;
//                         alert(message);
//                         error = true;
//                         return commonService.showError(message);
//                     } else {
//                         if (oneField.selectedChoice !== "any") {
//                             validDataSet["inputs"][oneField.name] = oneField.selectedChoice;
//                         }
//
//                     }
//                 });
//                 if (!error) {
//                     if(!$scope.addDataSet.name) {
//                         let message = "Please provide a name for the data-set";
//                         alert(message);
//                         error = true;
//                         return commonService.showError(message);
//                     } else {
//                         validDataSet["name"] = $scope.addDataSet.name;
//                         validDataSet["output"]["name"] = $scope.addDataSet["output"].name;
//                         validDataSet["output"]["min"] = $scope.addDataSet["output"].min;
//                         validDataSet["output"]["max"] = $scope.addDataSet["output"].max;
//                     }
//
//                 }
//             }
//
//             if (!error) {
//                 $scope.previewDataSets.push(validDataSet);
//                 $scope.addDataSet = null;
//             }
//
//         };
//
//
//         $scope.removeClick = (index) => {
//             //$scope.copyChartInfo.data_sets.splice(index, 1);
//             $scope.previewDataSets.splice(index, 1);
//                 //= $scope.copyChartInfo.data_sets;
//         };
//
//         $scope.submit = () => {
//             //$scope.previewDataSets = $scope.copyChartInfo.data_sets;
//             let payload = {};
//             payload["internal_chart_name"] = $scope.internalChartName;
//             payload["metric_model_name"] = $scope.modelName;
//             payload["chart_name"] = $scope.chartName;
//             payload["data_sets"] = $scope.previewDataSets;
//             payload["negative_gradient"] = $scope.negativeGradient;
//             payload["y1_axis_title"] = $scope.y1AxisTitle;
//             payload["y2_axis_title"] = $scope.y2AxisTitle;
//             payload["source"] = $scope.source;
//             payload["owner_info"] = $scope.owner;
//             payload["leaf"] = true;
//             payload["base_line_date"] = $scope.baseLineDate;
//
//             commonService.apiPost('/metrics/update_chart', payload, "EditChart: Submit").then((data) => {
//                 if(data) {
//                     alert("Submitted");
//                     $modalInstance.dismiss('cancel');
//                 } else {
//                     alert("Submission failed. Please check alerts");
//                 }
//
//             });
//         }
//     }
// }
//
//
//
// angular.module('qa-dashboard').controller("metricsController", MetricsController);


