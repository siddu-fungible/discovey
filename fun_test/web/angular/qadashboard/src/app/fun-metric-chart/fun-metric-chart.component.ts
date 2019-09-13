import {Component, OnInit, Input, OnChanges} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {CommonService} from "../services/common/common.service";
import {Observable} from "rxjs";
import {switchMap} from "rxjs/operators";
import {PerformanceService} from "../performance/performance.service";

enum TimeMode {
  ALL = "all",
  WEEK = "week",
  MONTH = "month"
}

enum Platform {
  F1 = "F1",
  S1 = "S1"
}

enum ExpectedOperation {
  SAME_AS_F1 = "Same as F1",
  F1_BY_4 = "F1/4"
}

@Component({
  selector: 'fun-metric-chart',
  templateUrl: './fun-metric-chart.component.html',
  styleUrls: ['./fun-metric-chart.component.css']
})

export class FunMetricChartComponent implements OnInit, OnChanges {
  @Input() minimal: boolean = false;
  @Input() id: number = null;
  @Input() previewDataSets: any = null;
  @Input() buildInfo: any = null;

  lsfUrl = "http://palladium-jobs.fungible.local:8080/job/";
  versionUrl = "https://github.com/fungible-inc/FunOS/releases/tag/";
  suiteUrl = "http://integration.fungible.local/regression/suite_detail/";
  LOGS_DIR = "/static/logs";
  suiteLogsDir = "http://integration.fungible.local/regression/static_serve_log_directory/";

  TIMEZONE: string = "America/Los_Angeles";

  status: string = null;
  showingTable: boolean;
  showingConfigure: boolean;
  chartInfo: any;
  headers: any;
  data: any = {}; //used for fun table
  metricId: number;
  editingDescription: boolean = false;
  editingOwner: boolean = false;
  editingSource: boolean = false;
  inner: any = {};
  currentDescription: string;
  currentOwner: string;
  currentSource: string;
  waitTime: number = 0;
  values: any;
  originalValues: any;
  charting: any;
  width: any;
  height: any;
  tableInfo: any;
  timeMode: string;
  negativeGradient: boolean;
  leaf: boolean;
  title: any;
  series: any;
  filterDataSets: any;
  chart1XaxisTitle: any;
  chart1YaxisTitle: any;
  y1AxisTitle: any;
  chartName: string;
  platform: string;
  modelName: string;
  pointClicked: boolean = false;
  pointInfo: any;
  buildProps: any;
  showBuildProps: boolean = false;
  paddingNeeded: boolean = false;
  mileStoneMarkers: any = {}; // fetch the milestones for each chart from backend and save it
  mileStoneIndices: any = {}; // fun-chart requires indices to plot lines on xaxis
  expectedValues: any = [];
  showAllExpectedValues: boolean = false;
  y1AxisPlotLines: any = []; //used to send the expected values plotlines to the fun chart
  showSelect: boolean = false;
  //used for determining the display range max of the charts
  maxDataSet: number = null; // maximum value of all the 'max' values of the datasets
  maxExpected: number = null; // maximum value of all the 'expected' values of the datasets
  maxDataPoint: number = null; // maximum value of all the data points from all the datasets
  originalMaxDataPoint: number = null;//when the unit changes, restore to original max
  minDataSet: number = null;
  yMax: number = null;
  yMin: number = null;
  yAxisSet: any = new Set(); //to cehck for duplicates in the expected value so that the text is not overwritten
  backgroundColor: string = "#FAFAFA";
  seriesColors: string[] = ['#058DC7', '#8B4513', '#ED561B', '#008000', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FD3A94', '#6AF9C4'];

  baseLineDate: string = null;
  visualizationUnit: string = null;
  changingVizUnit: string = null;
  expectedOperation: String = null;
  selectedUnit: string = null;
  category: string[] = [];

  Platform = Platform;

  //category of the units for the unit conversion
  latency_category: string[] = ["nsecs", "usecs", "msecs", "secs"];
  ops_category: string[] = ["ops", "Kops", "Mops", "Gops"];
  operations_category: string[] = ["op", "Kop", "Mop", "Gop"];
  cycles_category: string[] = ["cycles"];
  bits_bytes_category: string[] = ["b", "B", "KB", "MB", "GB", "TB"];
  bandwidth_category: string[] = ["bps", "Kbps", "Mbps", "Gbps", "Tbps", "Bps", "KBps", "MBps", "GBps", "TBps"];
  packets_per_second_category: string[] = ["Mpps", "pps", "Kpps", "Gpps"];
  connections_per_second_category: string[] = ["Mcps", "cps", "Kcps", "Gcps"];

  expectedOperationCategory: string[] = [ExpectedOperation.SAME_AS_F1, ExpectedOperation.F1_BY_4];

  triageInfo: any = null;
  successCommit: string = null;
  faultyCommit: string = null;
  faultyMessage: string = null;
  successMessage: string = null;
  faultyAuthor: string = null;
  successAuthor: string = null;
  commits: any = null;
  message: any = null;
  readonly DECIMAL_PRECISION: number = 5;

  containerMax: number = 200;

  public formatter: Function;
  public tooltip: Function;
  public pointClickCallback: Function;

  constructor(private apiService: ApiService, private loggerService: LoggerService, private route: ActivatedRoute,
              private commonService: CommonService, private performanceService: PerformanceService) {
  }

  ngOnInit() {
    this.status = "Updating";
    this.showingTable = false;
    this.showingConfigure = false;
    this.headers = null;
    this.metricId = -1;
    this.editingDescription = false;
    this.editingOwner = false;
    this.editingSource = false;
    this.inner = {};
    this.inner.currentDescription = "TBD";
    this.inner.currentOwner = "Unknown";
    this.currentOwner = "Unknown";
    this.inner.currentSource = "Unknown";
    this.currentSource = "Unknown";
    this.currentDescription = "---";
    this.values = null;
    this.charting = true;
    this.formatter = this.xAxisFormatter.bind(this);
    this.tooltip = this.tooltipFormatter.bind(this);
    this.pointClickCallback = this.pointDetail.bind(this);
    if (!this.buildInfo) {
      new Observable(observer => {
        observer.next(true);
        observer.complete();
        return () => {
        }
      }).pipe(
        switchMap(response => {
          return this.performanceService.fetchBuildInfo();
        })).subscribe(response => {
        this.buildInfo = response;
        console.log("fetched buildInfo");
      }, error => {
        this.loggerService.error("Unable to fetch buildInfo");
      });
    }
    if (!this.id) {
      this.status = null;
      this.fetchNames();
    }
  }

  ngOnChanges() {
    this.status = "Updating";
    this.fetchNames();
  }

  showPointDetails(pointInfo): void {
    let self = this;
    self.pointInfo = [];
    self.buildProps = [];
    Object.keys(pointInfo).forEach((key) => {
      if (key === "Build Properties") {
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
      this.platform = data.data["platform"];
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
        this.paddingNeeded = true;
        this.id = params['id'];
        this.fetchMetricsById();
      } else if (this.id) {
        this.fetchMetricsById();
      } else {
        this.status = null;
      }

    });
  }

  //formats the string displayed on xaxis of the chart
  xAxisFormatter(value): string {
    // value = "3/19/2019, 4:49:31 PM"
    let s = "Error";
    const monthNames = ["null", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    if (value) { //check for null values
      try {
        let dateString = value.split(" "); // ex: dateString = (3) ["3/19/2019,", "4:49:31", "PM"]
        let dateMonth = dateString[0].split("/"); //ex: dateMonth = (3) ["3", "19", "2019,"]
        if (this.timeMode === "month") {
          let month = parseInt(dateMonth[0]);
          s = monthNames[month]; //ex: s = "Apr"
        } else {
          s = dateMonth[0] + "/" + dateMonth[1]; //ex: s = "3/19"
        }
      } catch (e) {
        this.loggerService.error("xAxis Formatter");
      }
    }
    return s;
  }

  //checks if the given fieldname is relevant to display in show tables
  isFieldRelevant(fieldName): boolean {
    let relevant = false;
    this.filterDataSets.forEach((oneDataSet) => {
      Object.keys(oneDataSet.inputs).forEach((key) => {
        if (key === fieldName) {
          relevant = true;
        }
      });
      if (fieldName === oneDataSet.output.name || fieldName === "input_date_time" || fieldName === oneDataSet.output.name + "_unit") {
        relevant = true;
      }
    });
    return relevant;
  }

  //formats the tooltip shown in the charts
  tooltipFormatter(x, y, metaData): string {
    let softwareDate = "Unknown";
    let hardwareVersion = "Unknown";
    let sdkBranch = "Unknown";
    let gitCommit = "Unknown";
    let key = this._getBuildKey(x);
    let s = "";
    if (x) {
      s += "<b>Date:</b> " + x.substring(0, 5) + "<br>";
    }
    if (metaData.originalValue) {
      s += "<b>Value:</b> " + metaData.originalValue + "<br>";
    } else {
      s += "<b>Value:</b> " + y + "<br>";
    }
    return s;
  }

  //display details about the points in the chart
  pointDetail(x, y, metaData): any {
    let softwareDate = "Unknown";
    let hardwareVersion = "Unknown";
    let sdkBranch = "Unknown";
    let gitCommit = "Unknown";
    //let key = this._getBuildKey(x);
    let key = x;
    let s = {};
    let keyDate = new Date(key);
    let workAroundDate = new Date(2019, 6, 27);
    // TODO: workaround due to https://github.com/fungible-inc/Integration/pull/691
    if (keyDate < workAroundDate) {
      key = key.replace(/..$/, "00");
    }

    if (this.buildInfo && key in this.buildInfo) {
      softwareDate = this.buildInfo[key]["software_date"];
      hardwareVersion = this.buildInfo[key]["hardware_version"];
      sdkBranch = this.buildInfo[key]["fun_sdk_branch"];
      let buildProperties = this.buildInfo[key]["build_properties"];
      let lsfJobId = this.buildInfo[key]["lsf_job_id"];
      let version = this.buildInfo[key]["sdk_version"];
      let suiteExecutionId = this.buildInfo[key]["suite_execution_id"];
      let associatedSuites = this.buildInfo[key]["associated_suites"];
      if (sdkBranch !== "") {
        s["SDK branch"] = sdkBranch;
      }
      if (lsfJobId !== "") {
        s["Lsf job id"] = lsfJobId;
      }
      if (suiteExecutionId !== -1) {
        s["Suite execution detail"] = suiteExecutionId;
        s["Suite log directory"] = suiteExecutionId;
      }
      if (associatedSuites.length !== 0) {
        s["Associated suites"] = associatedSuites;
      }
      if (Number(softwareDate) > 0) {
        s["Software date"] = softwareDate;
      }
      if (hardwareVersion !== "") {
        s["Hardware version"] = hardwareVersion;
      }
      if (version !== "") {
        s["SDK version"] = "bld_" + version;
      }
      if (this.buildInfo[key]["git_commit"] !== "") {
        s["Git commit"] = this.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "");
      }
      if (buildProperties !== "") {
        s["Build Properties"] = buildProperties;
      }
    }
    if (x) {
      s["Date"] = x.substring(0, 5);
    }
    if (metaData.originalValue) {
      s["Value"] = metaData.originalValue;
    } else {
      s["Value"] = y;
    }
    return s;
  }

  _getBuildKey(x): string {
    let xDate = new Date(x).toISOString();
    xDate = xDate.replace("T", " ");
    let key = "";
    try {
      let dateString = xDate.split('.')[0];
      // key = dateString.slice(0, -2) + '00'; //added since the past values do not have accurate timestamp
      key = dateString; //removed the completion date and is dependent on build date
    }
    catch (e) {
      this.loggerService.error("Date on xAxis is empty for tooltip and point click call back");
    }
    return key;
  }

  // populates chartInfo and fetches metrics data
  fetchInfo(): void {
    let payload = {};
    // payload["metric_model_name"] = this.modelName;
    // payload["chart_name"] = this.chartName;
    payload["metric_id"] = this.id;
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
        this.currentOwner = this.chartInfo.owner_info;
        this.currentSource = this.chartInfo.source;
        this.inner.currentOwner = this.currentOwner;
        this.inner.currentSource = this.currentSource;
        this.negativeGradient = !this.chartInfo.positive;
        this.inner.negativeGradient = this.negativeGradient;
        this.leaf = this.chartInfo.leaf;
        this.inner.leaf = this.leaf;
        this.mileStoneMarkers = this.chartInfo.milestone_markers;
        this.baseLineDate = String(this.chartInfo.base_line_date);
        this.visualizationUnit = this.chartInfo.visualization_unit;
        this.changingVizUnit = this.visualizationUnit;
        this.chart1YaxisTitle = this.chartInfo.y1_axis_title;

        if (this.latency_category.includes(this.visualizationUnit)) {
          this.category = [...this.latency_category];
        } else if (this.bandwidth_category.includes(this.visualizationUnit)) {
          this.category = [...this.bandwidth_category];
        } else if (this.cycles_category.includes(this.visualizationUnit)) {
          this.category = [...this.cycles_category];
        } else if (this.operations_category.includes(this.visualizationUnit)) {
          this.category = [...this.operations_category];
        } else if (this.bits_bytes_category.includes(this.visualizationUnit)) {
          this.category = [...this.bits_bytes_category];
        } else if (this.ops_category.includes(this.visualizationUnit)) {
          this.category = [...this.ops_category];
        } else if (this.packets_per_second_category.includes(this.visualizationUnit)) {
          this.category = [...this.packets_per_second_category];
        } else if (this.connections_per_second_category.includes(this.visualizationUnit)) {
          this.category = [...this.connections_per_second_category];
        }
        this.selectedUnit = this.visualizationUnit;
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
    this.mileStoneIndices = {};
    this.showingTable = false;
    this.showingConfigure = false;
    this.pointClicked = false;
    this.showBuildProps = false;
    this.editingOwner = false;
    this.editingSource = false;
    this.editingDescription = false;
    this.chart1YaxisTitle = "";
    this.y1AxisPlotLines = [];
    this.yAxisSet = new Set();
    this.showAllExpectedValues = false;
    this.showSelect = false;
    this.yMax = null;
    this.yMin = null;
    this.series = null;
    this.values = null;
    this.maxDataSet = null;
    this.minDataSet = null;
    this.maxExpected = null;
    this.maxDataPoint = null;
    this.category = [];
    this.selectedUnit = null;
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

  convertExpected(): void {
    for (let dataSet of this.previewDataSets) {
      if (dataSet.output.max && dataSet.output.max !== -1) {
        dataSet.output.max = this.convertToBaseUnit(this.visualizationUnit, dataSet.output.max);
        dataSet.output.max = this.convertToVisualizationUnit(this.changingVizUnit, dataSet.output.max);
      }
      if (dataSet.output.expected && dataSet.output.expected !== -1) {
        dataSet.output.expected = this.convertToBaseUnit(this.visualizationUnit, dataSet.output.expected);
        dataSet.output.expected = this.convertToVisualizationUnit(this.changingVizUnit, dataSet.output.expected);
      }
      if (dataSet.output.reference && dataSet.output.reference !== -1) {
        dataSet.output.reference = this.convertToBaseUnit(this.visualizationUnit, dataSet.output.reference);
        dataSet.output.reference = this.convertToVisualizationUnit(this.changingVizUnit, dataSet.output.reference);
      }
    }
  }

  _setDataSetsDefaults(): void {
    for (let dataSet of this.previewDataSets) {
      if (!dataSet.output.max && this.leaf)
        dataSet.output.max = -1;
      if (!dataSet.output.max && !this.leaf)
        dataSet.output.max = this.containerMax;
      if (!dataSet.output.min)
        dataSet.output.min = 0;
      if (!dataSet.output.reference && this.leaf)
        dataSet.output.reference = -1;
      if (!dataSet.output.expected && this.leaf)
        dataSet.output.expected = -1;
    }
  }

  //saves the edited data back to the DB
  submit(): void {
    // this.convertExpected();
    this._setDataSetsDefaults();
    let payload = {};
    payload["metric_model_name"] = this.modelName;
    payload["chart_name"] = this.chartName;
    payload["metric_id"] = this.id;
    payload["data_sets"] = this.previewDataSets;
    payload["description"] = this.inner.currentDescription;
    payload["owner_info"] = this.inner.currentOwner;
    payload["source"] = this.inner.currentSource;
    payload["negative_gradient"] = this.inner.negativeGradient;
    payload["leaf"] = this.inner.leaf;
    payload["base_line_date"] = this.baseLineDate;
    payload["visualization_unit"] = this.changingVizUnit;
    payload["set_expected"] = this.expectedOperation;
    this.apiService.post('/metrics/update_chart', payload).subscribe((data) => {
      if (data.data) {
        this.editingDescription = false;
        this.editingOwner = false;
        this.editingSource = false;
        this.visualizationUnit = this.changingVizUnit;
        this.setTimeMode(TimeMode.ALL);
        this.selectedUnit = this.visualizationUnit;
      } else {
        alert("Submission failed. Please check alerts");
      }
    }, error => {
      this.loggerService.error("EditChart: Submit");
    });

  }

  openTriaging(): void {
    let url = "/performance/atomic/" + this.metricId + "/triage";
    window.open(url, '_blank');
  }

  openSource(url): void {
    window.open(url, '_blank');
  }

  openLsfUrl(lsfId): void {
    window.open(this.lsfUrl + lsfId, '_blank');
  }

  openSuiteUrl(suiteId): void {
    window.open(this.suiteUrl + suiteId, '_blank');
  }

  openSuiteLog(suiteId): void {
    window.open(this.suiteLogsDir + suiteId, '_blank');
  }

  openVersionUrl(version): void {
    window.open(this.versionUrl + version, '_blank');
  }

  getAppName(source): string {
    let s = "Unknown";
    let sourceSplits = source.split("/");
    s = sourceSplits[sourceSplits.length - 1];
    return s;
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
    this.showAllExpectedValues = false;
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
      let latestDate = this.commonService.convertEpochToDate(dateList[i], this.TIMEZONE);
      let latestMonth = latestDate.getMonth();
      while (i >= 0) {
        let currentDate = this.commonService.convertEpochToDate(dateList[i], this.TIMEZONE);
        let currentMonth = currentDate.getMonth();
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
      // let firstString = dates[0];
      // let firstDate = new Date(firstString);
      let firstDate = this.commonService.convertEpochToDate(dates[0], this.TIMEZONE);
      let lastDate = new Date();
      lastDate.setHours(23, 59, 59);

      let currentDate = firstDate;
      let datesIndex = 0;
      while (currentDate <= lastDate) {
        let latestDate = null;
        if ((datesIndex < dates.length) && this.sameDay(this.commonService.convertEpochToDate(dates[datesIndex], this.TIMEZONE), currentDate)) {
          latestDate = dates[datesIndex];
          datesIndex++;
          while ((datesIndex < dates.length) && this.sameDay(this.commonService.convertEpochToDate(dates[datesIndex], this.TIMEZONE), currentDate)) {
            latestDate = dates[datesIndex];
            datesIndex++;
          }
        } else {
          let tempDate = currentDate;
          tempDate.setHours(0);
          tempDate.setMinutes(0);
          tempDate.setSeconds(1);
          latestDate = this.commonService.convertDateToEpoch(tempDate);
        }
        let pstDate = this.commonService.convertEpochToDate(latestDate, this.TIMEZONE);
        finalDates.push(latestDate);
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

  //change the output show of the expected value checkbox
  changeExpectedValueShow(output): void {
    output.show = !output.show;
    this.calculateYaxisPlotLines();
    this.showAllExpectedValues = (this.expectedValues.length === this.y1AxisPlotLines.length);
  }

  //change the show of all expected values using select or unselect all link
  changeAllExpectedValues(): void {
    this.showAllExpectedValues = !this.showAllExpectedValues;
    for (let output of this.expectedValues) {
      output.show = this.showAllExpectedValues;
    }
    this.calculateYaxisPlotLines();
  }

  // calculate the yaxis plotlines - horizontal lines that are to be seen on the chart
  calculateYaxisPlotLines(): void {
    this.expectedValues = [...this.expectedValues];
    this.y1AxisPlotLines = [];
    let maximum = null;
    this.yAxisSet = new Set();
    for (let dataset of this.expectedValues) {
      if (dataset.show) {
        let line = {};
        line["text"] = "Expected for " + dataset.name;
        line["value"] = dataset.value;
        if (maximum === null) {
          maximum = dataset.value;
        } else {
          if (dataset.value > maximum) {
            maximum = dataset.value;
          }
        }
        //check if the expected values already has duplicate so that the text is not overwritten
        if (this.yAxisSet.has(line["value"])) {
          for (let y1axis of this.y1AxisPlotLines) {
            if (line["value"] === y1axis["value"]) {
              y1axis["text"] += ", " + dataset.name;
            }
          }
        } else {
          this.yAxisSet.add(line["value"]);
          this.y1AxisPlotLines.push(line);
        }
      }
    }
    this.maxExpected = maximum;
    this.calculateMax();
    this.calculateMin();
  }

  // calculate the yMax which is the maximum number of the display range on y axis
  calculateMax(): void {
    if (this.maxExpected && this.maxExpected !== -1) {
      if (this.maxDataSet !== -1) {
        if (this.maxDataSet > this.maxExpected) {
          this.yMax = this.maxDataSet;
        } else {
          this.yMax = this.maxExpected;
        }
      } else {
        if (this.maxDataPoint > this.maxExpected) {
          this.yMax = this.maxDataPoint;
        } else {
          this.yMax = this.maxExpected;
        }
      }
    } else {
      this.yMax = null;
    }
    this.yMax = this.yMax + (Number(this.yMax) * 0.05);
  }

  // calculate the yMin which is the maximum number of the display range on y axis
  calculateMin(): void {
    if (this.minDataSet && this.minDataSet > 0) {
      this.yMin = this.minDataSet;
      // this.yMin = this.yMin - (Number(this.yMin) * 0.05);
    } else {
      this.yMin = null;
    }

  }

  //fetch the data from backend
  fetchData(metricId, chartInfo, previewDataSets, tableInfo) {
    let payload = {};
    // payload["metric_model_name"] = metricModelName;
    // payload["chart_name"] = chartName;
    payload["preview_data_sets"] = previewDataSets;
    payload["metric_id"] = metricId;
    if (chartInfo) {
      payload["metric_id"] = chartInfo["metric_id"];
      this.metricId = chartInfo["metric_id"];
    }
    if (this.modelName !== 'MetricContainer') {
      this.fetchLeafData(chartInfo, previewDataSets, tableInfo, payload);
    } else {
      this.fetchContainerData(chartInfo, previewDataSets, payload);
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
        let trimEmptyStartValues = false; //used for trimming the start of the charts from a non zero value
        for (let oneRecord of oneDataSet) {
          let outputName = this.filterDataSets[dataSetIndex].output.name;
          if (oneRecord[outputName] > 0) {
            trimEmptyStartValues = true;
          }
          if (trimEmptyStartValues) {
            keyList.push(oneRecord.epoch_time); //value = "3/19/2019, 4:49:31 PM"
            keyValue[dataSetIndex][oneRecord.epoch_time] = oneRecord;
          }

        }
        dataSetIndex++;
      }
      keyList.sort();
      keyList = this.fixMissingDates(keyList);
      let datesByTimeMode = this.getDatesByTimeMode(keyList);
      let chartDataSets = [];
      let seriesDates = [];
      this.expectedValues = [];
      this.maxDataSet = null;
      this.minDataSet = null;
      this.maxExpected = null;
      this.maxDataPoint = null;
      this.yMax = null;
      for (let j = 0; j < this.filterDataSets.length; j++) {
        let oneChartDataArray = [];
        let thisMinimum = this.filterDataSets[j].output.min;
        let thisMaximum = this.filterDataSets[j].output.max;
        let outputName = this.filterDataSets[j].output.name;
        let name = this.filterDataSets[j].name;
        let unit = this.filterDataSets[j].output.unit;
        let expected = filterDataSets[j].output.expected;
        for (let i = 0; i < datesByTimeMode.length; i++) {
          let output = null;
          let total = 0;
          let count = 0;
          let startIndex = datesByTimeMode[i][0];
          let endIndex = datesByTimeMode[i][1];
          let matchingDateFound = false;
          let pstEpochDate = this.commonService.convertEpochToDate(keyList[startIndex], this.TIMEZONE);
          let keyString = this.commonService.addLeadingZeroesToDate(pstEpochDate);
          seriesDates.push(keyString);

          Object.keys(this.mileStoneMarkers).forEach((mileStone) => {
            let mileStoneDate = this.commonService.convertToTimezone(this.mileStoneMarkers[mileStone], this.TIMEZONE);
            //comparing two date objects to get the f1 milestone incase of date mismatch
            let compareDate = this.commonService.convertEpochToDate(keyList[startIndex], this.TIMEZONE);
            if (this.sameDay(mileStoneDate, compareDate)) { // Tape-out and F1
              if (!this.mileStoneIndices.hasOwnProperty(mileStone)) {
                this.mileStoneIndices[mileStone] = startIndex;
              }
            } else if (compareDate >= mileStoneDate) {
              if (mileStone !== "Tape-out") {
                if (!this.mileStoneIndices.hasOwnProperty(mileStone)) {
                  this.mileStoneIndices[mileStone] = startIndex;
                }
              }
            }
          });

          while (startIndex >= endIndex) {
            if (keyValue[j][keyList[startIndex]]) {
              let oneRecord = keyValue[j][keyList[startIndex]];
              matchingDateFound = true;
              output = oneRecord[outputName];
              let unit = outputName + '_unit';
              let outputUnit = oneRecord[unit];
              if (output > 0) {
                if (outputUnit && outputUnit !== "" && outputUnit !== this.visualizationUnit) {
                  output = this.convertToBaseUnit(outputUnit, output);
                  output = this.convertToVisualizationUnit(this.visualizationUnit, output);
                }
                total += output;
                count++;
              }
            }
            startIndex--;
          }
          if (count !== 0) {
            output = total / count;
          }
          let result = this.getValidatedData(output, thisMinimum, thisMaximum);
          if (this.maxDataPoint === null) {
            this.maxDataPoint = result.y;
            this.originalMaxDataPoint = this.maxDataPoint;
          } else {
            if (result.y > this.maxDataPoint) {
              this.maxDataPoint = result.y;
              this.originalMaxDataPoint = this.maxDataPoint;
            }
          }
          oneChartDataArray.push(result);
        }
        let oneChartDataSet = {name: name, data: oneChartDataArray};
        chartDataSets.push(oneChartDataSet);
        let output = {};
        output["name"] = name;
        if (expected && expected !== -1) {
          output["value"] = this.convertToBaseUnit(unit, expected);
          output["value"] = this.convertToVisualizationUnit(this.visualizationUnit, output["value"]);
        } else {
          output["value"] = expected;
        }
        output["unit"] = this.visualizationUnit;
        output["show"] = false;
        if (!this.showSelect && output["value"] !== -1) {
          this.showSelect = true;
        }
        this.expectedValues.push(output);
        if (this.maxDataSet === null) {
          this.maxDataSet = thisMaximum;
        } else {
          if (thisMaximum > this.maxDataSet) {
            this.maxDataSet = thisMaximum;
          }
        }
        if (this.minDataSet === null && thisMinimum > 0) {
          this.minDataSet = thisMinimum;
        } else {
          if (thisMinimum > 0 && thisMinimum < this.minDataSet) {
            this.minDataSet = thisMinimum;
          }
        }
        if (this.maxExpected === null) {
          this.maxExpected = expected;
        } else {
          if (expected > this.maxExpected) {
            this.maxExpected = expected;
          }
        }
      }
      this.calculateMax();
      this.calculateMin();
      this.chart1YaxisTitle = this.visualizationUnit;
      this.series = seriesDates;
      this.values = chartDataSets.slice();
      this.originalValues = JSON.parse(JSON.stringify(this.values));
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
      // payload["metric_model_name"] = this.modelName;
      // payload["chart_name"] = this.chartName;
      payload["metric_id"] = this.id;
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
      this.changeAllExpectedValues();
    }, error => {
      this.loggerService.error("fetchMetricsData");
    });
    this.status = null;
  }

  convertToBaseUnit(outputUnit, output): any {
    if (this.latency_category.includes(outputUnit)) {
      if (outputUnit === "usecs") {
        output = output / Math.pow(10, 6);
      } else if (outputUnit === "msecs") {
        output = output / Math.pow(10, 3);
      } else if (outputUnit === "nsecs") {
        output = output / Math.pow(10, 9);
      }
    } else if (this.bandwidth_category.includes(outputUnit)) {
      if (outputUnit === "Kbps") {
        output = output * Math.pow(10, 3);
      } else if (outputUnit === "Mbps") {
        output = output * Math.pow(10, 6);
      } else if (outputUnit === "Gbps") {
        output = output * Math.pow(10, 9);
      } else if (outputUnit === "Tbps") {
        output = output * Math.pow(10, 12);
      } else if (outputUnit === "Bps") {
        output = output * 8;
      } else if (outputUnit === "KBps") {
        output = output * 8 * Math.pow(10, 3);
      } else if (outputUnit === "MBps") {
        output = output * 8 * Math.pow(10, 6);
      } else if (outputUnit === "GBps") {
        output = output * 8 * Math.pow(10, 9);
      } else if (outputUnit === "TBps") {
        output = output * 8 * Math.pow(10, 12);
      }

    } else if (this.operations_category.includes(outputUnit)) {
      if (outputUnit === "Kop") {
        output = output * Math.pow(10, 3);
      } else if (outputUnit === "Mop") {
        output = output * Math.pow(10, 6);
      } else if (outputUnit === "Gop") {
        output = output * Math.pow(10, 9);
      }
    } else if (this.bits_bytes_category.includes(outputUnit)) {
      if (outputUnit === "B") {
        output = output * 8;
      } else if (outputUnit === "KB") {
        output = output * 8 * Math.pow(10, 3);
      } else if (outputUnit === "MB") {
        output = output * 8 * Math.pow(10, 6);
      } else if (outputUnit === "GB") {
        output = output * 8 * Math.pow(10, 9);
      } else if (outputUnit === "TB") {
        output = output * 8 * Math.pow(10, 12);
      }

    } else if (this.ops_category.includes(outputUnit)) {
      if (outputUnit === "Kops") {
        output = output * Math.pow(10, 3);
      } else if (outputUnit === "Mops") {
        output = output * Math.pow(10, 6);
      } else if (outputUnit === "Gops") {
        output = output * Math.pow(10, 9);
      }
    } else if (this.packets_per_second_category.includes(outputUnit)) {
      if (outputUnit === "Mpps") {
        output = output * Math.pow(10, 6);
      } else if (outputUnit === "Kpps") {
        output = output * Math.pow(10, 3);
      } else if (outputUnit === "Gpps") {
        output = output * Math.pow(10, 9);
      }
    } else if (this.connections_per_second_category.includes(outputUnit)) {
      if (outputUnit === "Mcps") {
        output = output * Math.pow(10, 6);
      } else if (outputUnit === "Kcps") {
        output = output * Math.pow(10, 3);
      } else if (outputUnit === "Gcps") {
        output = output * Math.pow(10, 9);
      }
    }

    return output;
  }

  convertToVisualizationUnit(outputUnit, output): any {
    if (this.latency_category.includes(outputUnit)) {
      if (outputUnit === "usecs") {
        output = output * Math.pow(10, 6);
      } else if (outputUnit === "msecs") {
        output = output * Math.pow(10, 3);
      } else if (outputUnit === "nsecs") {
        output = output * Math.pow(10, 9);
      }
    } else if (this.bandwidth_category.includes(outputUnit)) {
      if (outputUnit === "Kbps") {
        output = output / Math.pow(10, 3);
      } else if (outputUnit === "Mbps") {
        output = output / Math.pow(10, 6);
      } else if (outputUnit === "Gbps") {
        output = output / Math.pow(10, 9);
      } else if (outputUnit === "Tbps") {
        output = output / Math.pow(10, 12);
      } else if (outputUnit === "Bps") {
        output = output / 8;
      } else if (outputUnit === "KBps") {
        output = output / (8 * Math.pow(10, 3));
      } else if (outputUnit === "MBps") {
        output = output / (8 * Math.pow(10, 6));
      } else if (outputUnit === "GBps") {
        output = output / (8 * Math.pow(10, 9));
      } else if (outputUnit === "TBps") {
        output = output / (8 * Math.pow(10, 12));
      }

    } else if (this.operations_category.includes(outputUnit)) {
      if (outputUnit === "Kop") {
        output = output / Math.pow(10, 3);
      } else if (outputUnit === "Mop") {
        output = output / Math.pow(10, 6);
      } else if (outputUnit === "Gop") {
        output = output / Math.pow(10, 9);
      }

    } else if (this.bits_bytes_category.includes(outputUnit)) {
      if (outputUnit === "B") {
        output = output / 8;
      } else if (outputUnit === "KB") {
        output = output / (8 * Math.pow(10, 3));
      } else if (outputUnit === "MB") {
        output = output / (8 * Math.pow(10, 6));
      } else if (outputUnit === "GB") {
        output = output / (8 * Math.pow(10, 9));
      } else if (outputUnit === "TB") {
        output = output / (8 * Math.pow(10, 12));
      }

    } else if (this.ops_category.includes(outputUnit)) {
      if (outputUnit === "Kops") {
        output = output / Math.pow(10, 3);
      } else if (outputUnit === "Mops") {
        output = output / Math.pow(10, 6);
      } else if (outputUnit === "Gops") {
        output = output / Math.pow(10, 9);
      }
    } else if (this.packets_per_second_category.includes(outputUnit)) {
      if (outputUnit === "Mpps") {
        output = output / Math.pow(10, 6);
      } else if (outputUnit === "Kpps") {
        output = output / Math.pow(10, 3);
      } else if (outputUnit === "Gpps") {
        output = output / Math.pow(10, 9);
      }
    } else if (this.connections_per_second_category.includes(outputUnit)) {
      if (outputUnit === "Mcps") {
        output = output / Math.pow(10, 6);
      } else if (outputUnit === "Kcps") {
        output = output / Math.pow(10, 3);
      } else if (outputUnit === "Gcps") {
        output = output / Math.pow(10, 9);
      }
    }
    return parseFloat(output.toFixed(this.DECIMAL_PRECISION));
  }

  onUnitChange(newUnit) {
    // console.log(newUnit);
    this.chart1YaxisTitle = newUnit;
    let maximum = null;
    this.selectedUnit = newUnit;
    if (this.selectedUnit !== this.visualizationUnit) {
      this.values = JSON.parse(JSON.stringify(this.originalValues));
      let values = JSON.parse(JSON.stringify(this.values));
      for (let value of values) {
        for (let output of value.data) {
          if (output.y && output.y !== 0) {
            output.y = this.convertToBaseUnit(this.visualizationUnit, output.y);
            output.y = this.convertToVisualizationUnit(this.selectedUnit, output.y);
            if (output.y > maximum) {
              maximum = output.y;
            }
          }
        }
      }
      this.values = JSON.parse(JSON.stringify(values));
    } else {
      this.values = JSON.parse(JSON.stringify(this.originalValues));
    }
    for (let output of this.expectedValues) {
      if (output.value && output.value !== -1) {
        output.value = this.convertToBaseUnit(output.unit, output.value);
        output.value = this.convertToVisualizationUnit(this.selectedUnit, output.value);
        output.unit = this.selectedUnit;
      }
    }
    if (maximum === null) {
      this.maxDataPoint = this.originalMaxDataPoint;
    } else {
      this.maxDataPoint = maximum;
    }
    this.calculateYaxisPlotLines();
  }


  //fetching container data
  fetchContainerData(chartInfo, previewDataSets, payload): void {
    //console.log("Fetch Scores");
    this.apiService.post('/metrics/scores', payload).subscribe((response: any) => {
      if (response.data.length === 0) {
        this.values = null;
        return;
      }
      let filterDataSets = [];
      if (previewDataSets) {
        filterDataSets = previewDataSets;
      } else {
        if (chartInfo) {
          filterDataSets = chartInfo['data_sets'];
        }
      }
      let thisMinimum = filterDataSets[0].output.min;
      let thisMaximum = filterDataSets[0].output.max;
      let values = [];
      let series = [];
      let keyValue = {};
      let keyList = Object.keys(response.data.scores);
      keyList.sort();
      let trimEmptyStartValues = false; //used for trimming the start of the charts from a non zero value
      for (let dateTime of keyList) {
        let d = new Date(1000 * Number(dateTime));
        if (response.data.scores[dateTime].score > 0) {
          trimEmptyStartValues = true;
        }
        if (trimEmptyStartValues) {
          let pstDate = this.commonService.convertToTimezone(d, this.TIMEZONE);
          let keyString = this.commonService.addLeadingZeroesToDate(pstDate);
          series.push(keyString);
          keyValue[keyString] = response.data.scores[dateTime].score;
        }
      }
      if (series.length === 0) {
        this.series = null;
        this.values = null;
      } else {
        // series = this.fixMissingDates(series);
        let dateSeries = [];
        let seriesRange = this.getDatesByTimeMode(series);
        for (let i = 0; i < seriesRange.length; i++) {
          let startIndex = seriesRange[i][0];
          let endIndex = seriesRange[i][1];
          let count = 0;
          let total = 0;
          dateSeries.push(series[startIndex]);
          Object.keys(this.mileStoneMarkers).forEach((mileStone) => {
            let markerDate = this.mileStoneMarkers[mileStone].split(" ")[0];
            if (series[startIndex].includes(markerDate)) { // Tape-out and F1
              this.mileStoneIndices[mileStone] = startIndex;
            }
          });
          while (startIndex >= endIndex) {
            if (keyValue[series[startIndex]] && keyValue[series[startIndex]] !== -1) {
              total += keyValue[series[startIndex]];
              count++;
            }
            startIndex--;
          }
          if (count !== 0) {
            let average = total / count;
            let result = this.getValidatedData(average, thisMinimum, thisMaximum);
            values.push(result);
          } else {
            values.push(null);
          }
        }
        this.values = [{data: values, name: "Scores"}];
        this.series = dateSeries;
      }
    });
    this.status = null;
  }

  //called from fetchInfo and setTimeMode
  fetchMetricsData(metricModelName, chartName, chartInfo, previewDataSets) {
    this.title = chartName;
    var self = this;
    if (!chartName) {
      return;
    }
    var self = this;
    if (this.modelName !== 'MetricContainer') {
      return this.apiService.get("/metrics/describe_table/" + this.modelName).subscribe(function (response) {
        self.tableInfo = response.data;
        self.fetchData(self.id, chartInfo, previewDataSets, self.tableInfo);
      }, error => {
        this.loggerService.error("fetchMetricsData");
      })
    } else {
      this.fetchData(this.id, chartInfo, previewDataSets, this.tableInfo);
    }
  }


  //creates the point values for the funchart
  getValidatedData(data, minimum, maximum): any {
    let result = data;
    if (data < 0) {
      data = null;
    }
    let i = 0;
    result = {
      y: data,
      marker: {
        radius: 3
      },
      metaData: {}
    };
    if (data > maximum && maximum !== -1) {
      result.y = maximum;
      result.marker['symbol'] = "url(/static/media/red-x-png-7.png)";
      result.marker.radius = 3;
      result.metaData["originalValue"] = data;
    }
    return result;
  }

}
