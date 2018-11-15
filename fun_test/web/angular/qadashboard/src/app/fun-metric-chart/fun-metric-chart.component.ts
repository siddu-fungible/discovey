import {Component, OnInit, Input, OnChanges} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'fun-metric-chart',
  templateUrl: './fun-metric-chart.component.html',
  styleUrls: ['./fun-metric-chart.component.css']
})
export class FunMetricChartComponent implements OnInit, OnChanges {
  @Input() minimal: boolean = false;
  @Input() id: number = null;
  @Input() previewDataSets: any = null;

  status: string = null;
  showingTable: boolean;
  showingConfigure: boolean;
  chartInfo: any;
  headers: any;
  data: any = {}; //used for fun table
  metricId: number;
  editingDescription: boolean = false;
  editingOwner: boolean = false;
  inner: any = {};
  currentDescription: string;
  currentOwner: string;
  waitTime: number = 0;
  values: any;
  charting: any;
  width: any;
  height: any;
  tableInfo: any;
  buildInfo: any;
  timeMode: string;
  negativeGradient: boolean;
  leaf: boolean;
  title: any;
  series: any;
  filterDataSets: any;
  chart1XaxisTitle: any;
  chart1YaxisTitle: any;
  y1AxisTitle: any;
  mileStoneIndex: number = null;
  chartName: string;
  modelName: string;
  pointClicked: boolean = false;
  pointInfo: any;
  buildProps: any;
  showBuildProps: boolean = false;

  public formatter: Function;
  public tooltip: Function;
  public pointClickCallback: Function;

  constructor(private apiService: ApiService, private loggerService: LoggerService, private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.status = "Updating";
    this.fetchNames();
    this.showingTable = false;
    this.showingConfigure = false;
    this.headers = null;
    this.metricId = -1;
    this.editingDescription = false;
    this.editingOwner = false;
    this.inner = {};
    this.inner.currentDescription = "TBD";
    this.inner.currentOwner = "Bertrand Serlet(bertrand.serlet@fungible.com)";
    this.currentDescription = "---";
    this.values = null;
    this.charting = true;
    this.buildInfo = null;
    this.fetchBuildInfo();
    this.formatter = this.xAxisFormatter.bind(this);
    this.tooltip = this.tooltipFormatter.bind(this);
    this.pointClickCallback = this.pointDetail.bind(this);
    this.status = null;
  }

  ngOnChanges() {
    this.status = "Updating";
    this.fetchNames();
    this.status = null;
  }

  showPointDetails(pointInfo): void {
    let self = this;
    self.pointInfo = [];
    self.buildProps = [];
    Object.keys(pointInfo).forEach((key) => {
        if(key === "Build Properties") {
          let properties = pointInfo[key];
          self.buildProps["name"] = key;
          self.buildProps["value"] = properties;
        } else {
          let property = [];
          property["name"] = key;
          property["value"] = pointInfo[key];
          self.pointInfo.push(property);
        }
    });
    self.pointClicked = true;
  }

  fetchMetricsById(): void {
    let payload = {};
    payload["metric_id"] = this.id;
    this.apiService.post('/metrics/metric_by_id', payload).subscribe((data) => {
      this.chartName = data.data["chart_name"];
      this.modelName = data.data["metric_model_name"];
      this.setDefault();
      this.fetchInfo();
    }, error => {
      this.loggerService.error("fetching by metric id failed");
    });
  }

  //set the chart and model name based in metric id
  fetchNames() {
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.id = params['id'];
        this.fetchMetricsById();
      }
      else if (this.id) {
        this.fetchMetricsById();
      }
    });
  }

  //formats the string displayed on xaxis of the chart
  xAxisFormatter(value): string {
    let s = "Error";
    const monthNames = ["null", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    let r = /(\d{4})-(\d{2})-(\d{2})/g;
    let match = r.exec(value);
    if (this.timeMode === "month") {
      if (match) {
        let month = parseInt(match[2]);
        s = monthNames[month];
      }
    } else {
      if (match) {
        s = match[2] + "/" + match[3];
      }
    }
    return s;
  }

  //checks if the given fieldname is relevant to display in show tables
  isFieldRelevant(fieldName): boolean {
    let relevant = false;
    if (fieldName === "input_date_time") {
      relevant = true;
    }
    this.filterDataSets.forEach((oneDataSet) => {
      Object.keys(oneDataSet.inputs).forEach((key) => {
        if (key === fieldName) {
          relevant = true;
        }
      });
      if (fieldName === oneDataSet.output.name) {
        relevant = true;
      }
    });
    return relevant;
  }

  //formats the tooltip shown in the charts
  tooltipFormatter(x, y): string {
    let softwareDate = "Unknown";
    let hardwareVersion = "Unknown";
    let sdkBranch = "Unknown";
    let gitCommit = "Unknown";
    let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
    let match = r.exec(x);
    let key = "";
    if (match) {
      key = match[1];
    } else {
      let reg = /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})/g;
      match = reg.exec(x);
      if (match) {
        key = match[1].replace('T', ' ');
      }
    }
    let s = "Error";
    if (this.buildInfo && key in this.buildInfo) {
      softwareDate = this.buildInfo[key]["software_date"];
      s = "<b>Software date:</b> " + softwareDate + "<br>";
      s += "<b>Value:</b> " + y + "<br>";
    } else {
      s = "<b>Value:</b> " + y + "<br>";
    }
    return s;
  }

  //display details about the points in the chart
  pointDetail(x, y): any {
    let softwareDate = "Unknown";
    let hardwareVersion = "Unknown";
    let sdkBranch = "Unknown";
    let gitCommit = "Unknown";
    let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
    let match = r.exec(x);
    let key = "";
    if (match) {
      key = match[1];
    } else {
      let reg = /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})/g;
      match = reg.exec(x);
      if (match) {
        key = match[1].replace('T', ' ');
      }
    }
    let s = {};
    if (this.buildInfo && key in this.buildInfo) {
      softwareDate = this.buildInfo[key]["software_date"];
      hardwareVersion = this.buildInfo[key]["hardware_version"];
      sdkBranch = this.buildInfo[key]["fun_sdk_branch"];
      let buildProperties = this.buildInfo[key]["build_properties"];
      s["SDK branch"] = sdkBranch;
      s["Software date"] = softwareDate;
      s["Hardware version"] = hardwareVersion;
      s["Git commit"] = this.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "");
      s["Build Properties"] = buildProperties;
      s["Value"] = y;
    } else {
      s["Value"] = y;
    }
    return s;
  }

  // populates chartInfo and fetches metrics data
  fetchInfo(): void {
    let payload = {};
    payload["metric_model_name"] = this.modelName;
    payload["chart_name"] = this.chartName;
    this.apiService.post("/metrics/chart_info", payload).subscribe((response) => {
      this.chartInfo = response.data;
      if (this.chartInfo !== null) {
        this.previewDataSets = this.getPreviewDataSets();
        if (!this.previewDataSets) {
          this.loggerService.error("No Preview Datasets");
          return;
        }
        this.currentDescription = this.chartInfo.description;
        this.inner.currentDescription = this.currentDescription;
        this.negativeGradient = !this.chartInfo.positive;
        this.inner.negativeGradient = this.negativeGradient;
        this.leaf = this.chartInfo.leaf;
        this.inner.leaf = this.leaf;
      }
      setTimeout(() => {
        this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, this.previewDataSets);
      }, this.waitTime);
    }, error => {
      this.loggerService.error("fun_metric_chart: chart_info");
    });
  }

  //sets the state of the component to default values
  setDefault(): void {
    this.timeMode = "all";
    this.mileStoneIndex = null;
    this.showingTable = false;
    this.showingConfigure = false;
    this.pointClicked = false;
    this.showBuildProps = false;
  }

  closePointInfo(): void {
    this.pointClicked = false;
    this.showBuildProps = false;
  }
  getPreviewDataSets(): any {
    return this.chartInfo.data_sets;
  }

  //closes the div of show tables
  close() {
    this.showingTable = false;
  }

  //toggles the div of description below the chart
  toggleEdit() {
    this.editingDescription = !this.editingDescription;
  }

  toggleOwner() {
    this.editingOwner = !this.editingOwner;
  }

  //shows the shortened date in show tables
  cleanValue(key, value): any {
    try {
      if (key === "input_date_time") {
        let s = "Error";
        let r = /(\d{4})-(\d{2})-(\d{2})/g;
        let match = r.exec(value);
        if (match) {
          s = match[2] + "/" + match[3];
        }
        return s;
      } else {
        return value;
      }
    } catch (e) {
    }
  }

  //saves the edited data back to the DB
  submit(): void {
    let payload = {};
    payload["metric_model_name"] = this.modelName;
    payload["chart_name"] = this.chartName;
    payload["data_sets"] = this.previewDataSets;
    payload["description"] = this.inner.currentDescription;
    payload["negative_gradient"] = this.inner.negativeGradient;
    payload["leaf"] = this.inner.leaf;
    this.apiService.post('/metrics/update_chart', payload).subscribe((data) => {
      if (data) {
        alert("Submitted");
      } else {
        alert("Submission failed. Please check alerts");
      }
    }, error => {
      this.loggerService.error("EditChart: Submit");
    });
    this.editingDescription = false;
  }

  //populates buildInfo
  fetchBuildInfo(): void {
    this.apiService.get('/regression/build_to_date_map').subscribe((response) => {
      this.buildInfo = response.data;
    }, error => {
      this.loggerService.error("regression/build_to_date_map");
    });
  }

  //opens and closes the show tables panel
  showTables(): void {
    this.showingTable = !this.showingTable;
  }

  //opens and closes the show configure panel
  showConfigure(): void {
    this.showingConfigure = !this.showingConfigure;
  }

  //invoked when timeMode changes
  setTimeMode(mode): void {
    this.timeMode = mode;
    if (this.chartInfo) {
      this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, this.previewDataSets); // TODO: Race condition on chartInfo
    } else {
      this.fetchMetricsData(this.modelName, this.chartName, null, this.previewDataSets); // TODO: Race condition on chartInfo
    }
  }

  //returns the range of dates according to the time mode
  getDatesByTimeMode(dateList): any {
    let len = dateList.length;
    let filteredDate = [];
    let result = [[len, 0]];
    if (this.timeMode === "week") {
      for (let i = len - 1; i >= 0; i = i - 7) {
        if (i >= 7) {
          filteredDate.push([i, i - 7 + 1]);
        }
        else {
          filteredDate.push([i, 0]);
        }
      }
      result = filteredDate.reverse();
    } else if (this.timeMode === "month") {
      let i = len - 1;
      let startIndex = len - 1;
      let latestDate = new Date(dateList[i].replace(/\s+/g, 'T'));
      let latestMonth = latestDate.getUTCMonth();
      while (i >= 0) {
        let currentDate = new Date(dateList[i].replace(/\s+/g, 'T'));
        let currentMonth = currentDate.getUTCMonth();
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
    } else {
      for (let i = len - 1; i >= 0; i--) {
        filteredDate.push([i, i]);
      }
      result = filteredDate.reverse();
    }
    return result;
  }

  //check for all dates and if not present add the respective date to the list
  fixMissingDates(dates): any {
    let finalDates = [];
    if (dates.length !== 0) {
      let firstString = dates[0].replace(/\s+/g, 'T');
      //firstString = firstString.replace('+', 'Z');
      //firstString = firstString.substring(0, firstString.indexOf('Z'));
      let firstDate = new Date(firstString);
      let today = new Date();
      let yesterday = new Date(today);
      // yesterday.setDate(yesterday.getDate() - 1);
      // yesterday.setHours(23, 59, 59);
      let lastDate = yesterday;

      let currentDate = firstDate;
      let datesIndex = 0;
      while (currentDate <= yesterday) {

        //console.log(currentDate);
        if ((datesIndex < dates.length) && this.sameDay(new Date(dates[datesIndex].replace(/\s+/g, 'T')), currentDate)) {
          finalDates.push(dates[datesIndex]);
          datesIndex++;
          while ((datesIndex < dates.length) && this.sameDay(new Date(dates[datesIndex].replace(/\s+/g, 'T')), currentDate)) {
            //finalDates.push(dates[datesIndex]);
            datesIndex++;
          }
        } else {
          //currentDate.setHours(currentDate.getHours() - currentDate.getTimezoneOffset() / 60);
          let tempDate = currentDate;
          tempDate.setHours(0);
          tempDate.setMinutes(0);
          tempDate.setSeconds(1);
          tempDate = new Date(tempDate.getTime() - (tempDate.getTimezoneOffset() * 60000));
          finalDates.push(tempDate.toISOString().replace('T', ' ')); //TODO: convert zone correctly
        }
        currentDate.setDate(currentDate.getDate() + 1);
      }
    }
    return finalDates;
  }

  //check if both the dates are same
  sameDay(d1, d2) {
    return d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate();
  }

  //fetch the data from backend
  fetchData(metricModelName, chartName, chartInfo, previewDataSets, tableInfo) {
    let payload = {};
    payload["metric_model_name"] = metricModelName;
    payload["chart_name"] = chartName;
    payload["preview_data_sets"] = previewDataSets;
    payload["metric_id"] = -1;
    if (chartInfo) {
      payload["metric_id"] = chartInfo["metric_id"];
      this.metricId = chartInfo["metric_id"];
    }
    if (metricModelName !== 'MetricContainer') {
      this.fetchLeafData(chartInfo, previewDataSets, tableInfo, payload);
    } else {
      this.fetchContainerData(payload);
    }
  }

  //fetching leaf data
  fetchLeafData(chartInfo, previewDataSets, tableInfo, payload): void {
    this.tableInfo = tableInfo;
    let filterDataSets = [];
    if (previewDataSets) {
      filterDataSets = previewDataSets;
    } else {
      if (chartInfo) {
        filterDataSets = chartInfo['data_sets'];
      }
    }
    this.filterDataSets = filterDataSets;
    this.apiService.post("/metrics/data", payload).subscribe((response: any) => {
      let allDataSets = response.data;
      if (allDataSets.length === 0) {
        this.values = null;
        return;
      }
      let keyList = [];
      let keyValue = [];
      let dataSetIndex = 0;
      for (let oneDataSet of allDataSets) {
        keyValue[dataSetIndex] = [];
        for (let oneRecord of oneDataSet) {
          keyList.push(oneRecord.input_date_time.toString());
          keyValue[dataSetIndex][oneRecord.input_date_time.toString()] = oneRecord;
        }
        dataSetIndex++;
      }
      keyList.sort();
      keyList = this.fixMissingDates(keyList);
      let originalKeyList = keyList;
      keyList = this.getDatesByTimeMode(keyList);
      let chartDataSets = [];
      let seriesDates = [];
      for (let j = 0; j < this.filterDataSets.length; j++) {
        let oneChartDataArray = [];
        for (let i = 0; i < keyList.length; i++) {
          let output = null;
          let total = 0;
          let count = 0;
          let startIndex = keyList[i][0];
          let endIndex = keyList[i][1];
          let matchingDateFound = false;
          seriesDates.push(originalKeyList[startIndex]);
          if (originalKeyList[startIndex].includes("2018-09-16")) { // Tape-out
            this.mileStoneIndex = startIndex;
          }
          while (startIndex >= endIndex) {
            if (keyValue[j][originalKeyList[startIndex]]) {
              let oneRecord = keyValue[j][originalKeyList[startIndex]];
              matchingDateFound = true;
              let outputName = this.filterDataSets[j].output.name;
              output = oneRecord[outputName];
              total += output;
              count++;
              if (chartInfo && chartInfo.y1_axis_title) {
                this.chart1YaxisTitle = chartInfo.y1_axis_title;
              } else {
                this.chart1YaxisTitle = tableInfo[outputName].verbose_name;
              }
              if (this.y1AxisTitle) {
                this.chart1YaxisTitle = this.y1AxisTitle;
              }
              this.chart1XaxisTitle = tableInfo["input_date_time"].verbose_name;
            }
            startIndex--;
          }
          if (count !== 0) {
            output = total / count;
          }
          let thisMinimum = this.filterDataSets[j].output.min;
          let thisMaximum = this.filterDataSets[j].output.max;
          oneChartDataArray.push(this.getValidatedData(output, thisMinimum, thisMaximum));
        }
        let oneChartDataSet = {name: this.filterDataSets[j].name, data: oneChartDataArray};
        chartDataSets.push(oneChartDataSet);
      }
      this.series = seriesDates;
      this.values = chartDataSets;
      this.headers = this.tableInfo;
      //this.data has values for the fun table
      this.data["rows"] = [];
      this.data["headers"] = [];
      this.data["all"] = true;
      this.data["pageSize"] = 10;
      this.data["currentPageIndex"] = 1;
      Object.keys(this.headers).forEach((key) => {
        if (this.isFieldRelevant(key)) {
          this.data["headers"].push(this.headers[key].verbose_name);
        }
      });
      // let dataSet = allDataSets[0];
      let index = 0;
      let self = this;
      let payload = {};
      payload["metric_model_name"] = this.modelName;
      payload["chart_name"] = this.chartName;
      payload["preview_data_sets"] = this.filterDataSets;
      this.apiService.post("/metrics/data_by_model", payload).subscribe((response) => {
        let dataSet = response.data;
        for (let rowData of dataSet) {
          let row = [];
          let rowInTable = [];
          Object.keys(self.headers).forEach((key) => {
            if (self.isFieldRelevant(key)) {
              let value = rowData[key];
              rowInTable.push(value);
              row.push(self.cleanValue(key, value));
            }
          });
          self.data["rows"][index++] = rowInTable;
        }
        self.data["totalLength"] = self.data["rows"].length;
      });
    }, error => {
      this.loggerService.error("fetchMetricsData");
    });
  }

  //fetching container data
  fetchContainerData(payload): void {
    console.log("Fetch Scores");
    this.apiService.post('/metrics/scores', payload).subscribe((response: any) => {
      if (response.data.length === 0) {
        this.values = null;
        return;
      }
      let values = [];
      let series = [];
      let keyValue = {};
      let keyList = Object.keys(response.data.scores);
      keyList.sort();
      for (let dateTime of keyList) {
        let d = new Date(1000 * Number(dateTime)).toISOString();
        series.push(d);
        keyValue[d] = response.data.scores[dateTime].score;
      }
      if (series.length === 0) {
        this.series = null;
        this.values = null;
      } else {
        series = this.fixMissingDates(series);
        let dateSeries = [];
        let seriesRange = this.getDatesByTimeMode(series);
        for (let i = 0; i < seriesRange.length; i++) {
          let startIndex = seriesRange[i][0];
          let endIndex = seriesRange[i][1];
          let count = 0;
          let total = 0;
          dateSeries.push(series[startIndex]);
          if (series[startIndex].includes("2018-09-16")) { // Tape-out
            this.mileStoneIndex = startIndex;
          }
          while (startIndex >= endIndex) {
            if (keyValue[series[startIndex]] != -1) {
              total += keyValue[series[startIndex]];
              count++;
            }
            startIndex--;
          }
          if (count !== 0) {
            let average = total / count;
            values.push(average);
          } else {
            values.push(null);
          }
        }
        this.chart1YaxisTitle = "Scores";
        this.chart1XaxisTitle = "Date";
        this.values = [{data: values}];
        this.series = dateSeries;
      }
    });
  }

  //called from fetchInfo and setTimeMode
  fetchMetricsData(metricModelName, chartName, chartInfo, previewDataSets) {
    this.title = chartName;
    var self = this;
    if (!chartName) {
      return;
    }
    var self = this;
    if (metricModelName !== 'MetricContainer') {
      return this.apiService.get("/metrics/describe_table/" + metricModelName).subscribe(function (response) {
        self.tableInfo = response.data;
        self.fetchData(metricModelName, chartName, chartInfo, previewDataSets, self.tableInfo);
      }, error => {
        this.loggerService.error("fetchMetricsData");
      })
    } else {
      this.fetchData(metricModelName, chartName, chartInfo, previewDataSets, this.tableInfo);
    }
  }

  //creates the point values for the funchart
  getValidatedData(data, minimum, maximum): any {
    let result = data;
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
  }
}
