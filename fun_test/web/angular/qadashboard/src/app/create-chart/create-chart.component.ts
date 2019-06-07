import {Component, OnInit, Input, OnChanges} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'create-chart',
  templateUrl: './create-chart.component.html',
  styleUrls: ['./create-chart.component.css']
})
export class CreateChartComponent implements OnInit, OnChanges {
  xValues: any = [];
  title: string;
  xAxisLabel: string;
  // @Input() chartName: string;
  // @Input() modelName: string;
  // @Input() mode: string;
  y1AxisTitle: string = null;
  y2AxisTitle: string = null;
  chartInfo: any = null;
  copyChartInfo: any = null;
  previewDataSets: any = [];
  addDataSet: any = null;
  outputOptions: any = [];
  tableInfo: any = null;
  showOutputSelection: boolean;
  negativeGradient: boolean = false;
  inputNames: any;//name headers
  selectedOutput: any;
  mode: string = null;
  chartName: string = null;
  modelName: string = null;
  metricId: number = null;
  internalChartName: string = null;


  constructor(private apiService: ApiService, private logger: LoggerService, private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['mode']) {
        this.mode = params['mode'];
      }
      if (params['metricId']) {
        this.metricId = params['metricId']
      }
      if (params['modelName']) {
        this.modelName = params['modelName']
      }
    });
    this.showOutputSelection = false;

    if (this.metricId) {
      let payload = {};
      payload["metric_id"] = this.metricId;
      this.apiService.post("/metrics/chart_info", payload).subscribe((chartInfo) => {
        this.chartInfo = chartInfo.data;
        //this.copyChartInfo = angular.copy(this.chartInfo);
        this.previewDataSets = this.chartInfo.data_sets;
        this.negativeGradient = !this.chartInfo.positive;
        this.chartName = this.chartInfo.chart_name;
        this.y1AxisTitle = this.chartInfo.y1_axis_title;

      }, error => {
        this.logger.error("EditChartController: chart_info");
      });
    }
    this.describeTable();

  }

  ngOnChanges(){
  }

  describeTable = () => {
    this.inputNames = [];
    var self = this;
    this.apiService.get("/metrics/describe_table/" + this.modelName).subscribe(function (tableInfo) {
      self.tableInfo = tableInfo.data;
      Object.keys(self.tableInfo).forEach((field) => {
          let fieldInfo = self.tableInfo[field];
          let oneField = {};
        oneField["name"] = field;
        if ('choices' in fieldInfo && oneField["name"].startsWith("input")) {
          oneField["choices"] = fieldInfo.choices.map((choice) => {
            return choice[1]
          });
          self.inputNames.push(oneField);
        }
        if (oneField["name"].startsWith("output")) {
          self.outputOptions.push(oneField["name"]);
        }
      });
    }, error => {
      this.logger.error("describe table create chart");
    });
  };

  addDataSetClick = () => {
    this.showOutputSelection = true;
    if (!this.tableInfo) {
      return this.describeTable();
    }
    this.addDataSet = {};
    this.addDataSet["inputs"] = this.inputNames;
    this.addDataSet["output"] = {min: 0, max: 99999};
  };

  addClick = () => {
    let error = false;
    //
    let validDataSet = {};
    validDataSet["inputs"] = {};
    validDataSet["output"] = {};
    if (this.addDataSet) {
      // lets validate all inputs
      this.addDataSet["inputs"].forEach((oneField) => {
        if (!oneField.selectedChoice && oneField.name !== "input_date_time" && oneField.choices.length) {
          let message = "Please select a choice for " + oneField.name;
          alert(message);
          error = true;
          return this.logger.error(message);
        } else {
          validDataSet["inputs"][oneField.name] = oneField.selectedChoice;
        }
      });
      if (!error) {
        if (!this.addDataSet.name) {
          let message = "Please provide a name for the data-set";
          alert(message);
          error = true;
          this.logger.error(message);
        } else if (!this.addDataSet["output"].name) {
          let message = "Please select atleast one output";
          alert(message);
          error = true;
          this.logger.error(message);
        } else {
          validDataSet["name"] = this.addDataSet.name;
          validDataSet["output"]["name"] = this.addDataSet["output"].name;
          validDataSet["output"]["min"] = this.addDataSet["output"].min;
          validDataSet["output"]["max"] = this.addDataSet["output"].max;
        }

      }
    }

    if (!error) {
      // using temp to change the reference of previewdatasets so that the onchanges is triggered
      let temp = Object.assign([], this.previewDataSets);
      temp.push(validDataSet);
      this.previewDataSets = temp;
      this.showOutputSelection = false;
      // this.addDataSet = null;
    }

  };


  removeClick = (index) => {
     // using temp to change the reference of previewdatasets so that the onchanges is triggered
    this.previewDataSets.splice(index, 1);
    this.previewDataSets = Object.assign([], this.previewDataSets);
  };

  submit(): void {
    //this.previewDataSets = this.copyChartInfo.data_sets;
    let payload = {};
    payload["metric_model_name"] = this.modelName;
    payload["chart_name"] = this.chartName;
    payload["data_sets"] = this.previewDataSets;
    payload["negative_gradient"] = this.negativeGradient;
    payload["y1_axis_title"] = this.y1AxisTitle;
    payload["y2_axis_title"] = this.y2AxisTitle;
    payload["leaf"] = true;

    this.apiService.post('/metrics/update_chart', payload).subscribe((data) => {
      if (data) {
        alert("Submitted");
      } else {
        alert("Submission failed. Please check alerts");
      }

    }, error => {
      this.logger.error("EditChart: Submit");
    });
  }

  dismiss() {
    window.close();
  }
  
}
