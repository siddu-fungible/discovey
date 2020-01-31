import {Component, OnInit, Input, OnChanges} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {CommonService} from "../services/common/common.service";
import {Observable, of} from "rxjs";
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
  @Input() chartInfo: any = null;

  lsfUrl = "http://palladium-jobs.fungible.local:8080/job/";
  versionUrl = "https://github.com/fungible-inc/FunOS/releases/tag/";
  suiteUrl = "http://integration.fungible.local/regression/suite_detail/";
  LOGS_DIR = "/static/logs";
  suiteLogsDir = "http://integration.fungible.local/regression/static_serve_log_directory/";

  TIMEZONE: string = "America/Los_Angeles";
  daysInPast: number = 60;
  editingDaysInPast: boolean = false;
  showingAll: boolean = false;
  DEFAULT_DAYS_IN_PAST: number = 60;
  MAX_DAYS_IN_PAST: number = 120;
  allDataSets: any = null;

  status: string = null;
  showingTable: boolean;
  showingConfigure: boolean;
  headers: any;
  data: any = {}; //used for fun table
  metricId: number;
  editingDescription: boolean = false;
  editingOwner: boolean = false;
  editingSource: boolean = false;
  currentDescription: string = "TBD";
  currentOwner: string = "Unknown";
  currentSource: string = "Unknown";
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
  power_category: string[] = ["W", "kW", "MW", "mW"];

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
    this.daysInPast = this.DEFAULT_DAYS_IN_PAST;
    this.editingDaysInPast = false;
    this.headers = null;
    this.values = null;
    this.editingDescription = false;
    this.editingOwner = false;
    this.editingSource = false;
    this.charting = true;
    this.formatter = this.xAxisFormatter.bind(this);
    this.tooltip = this.tooltipFormatter.bind(this);
    this.pointClickCallback = this.pointDetail.bind(this);
    if (!this.id) {
      this.status = null;
      this.fetchNames();
    }
  }

  ngOnChanges() {
    this.daysInPast = this.DEFAULT_DAYS_IN_PAST;
    this.editingDaysInPast = false;
    this.refreshCharts();
  }

  refreshCharts() {
    this.status = "Updating";
    this.fetchNames();
  }

  submitDaysInPast(): void {
    this.refreshCharts();
  }

  setDaysInPast(daysInPast): void {
    if (daysInPast === this.DEFAULT_DAYS_IN_PAST) {
      this.showingAll = false;
      this.daysInPast = this.DEFAULT_DAYS_IN_PAST;
    } else {
      this.showingAll = true;
      this.daysInPast = this.MAX_DAYS_IN_PAST;
    }
    this.refreshCharts();
  }

  showPointDetails(point): void {
    let metaData = point["metaData"];
    let self = this;
    if (metaData.runTimeId) {
      let props = {};
      of (true).pipe(
        switchMap(response => {
          return this.performanceService.getRunTime(metaData.runTimeId);
        }),
        switchMap(response => {
          self.setPointInfo(response, point);
          return of(true);
        })
      ).subscribe(response => {
        self.pointClicked = true;
      }, error => {
        this.loggerService.error("Unable to fetch pointInfo from runtime metadata");
      });
    } else {
      self.setPointInfo(null, point);
      self.pointClicked = true;
    }
  }

  setPointInfo(props, point): any {
    let s = {};
    let self = this;
    self.pointInfo = {};
    self.buildProps = null;
    if (props) {
      if (props.jenkins_build_number) {
        self.pointInfo["Jenkins build number"] = props.jenkins_build_number;
      }
      if (props.lsf_job_id) {
        self.pointInfo["LSF job id"] = props.lsf_job_id;
      }
      if (props.suite_execution_id) {
        self.pointInfo["Suite execution id"] = props.suite_execution_id;
        self.pointInfo["Suite log directory"] = props.suite_execution_id;
      }
      if (props.version) {
        self.pointInfo["Version"] = "bld_" + props.version;
      }
      if (props.associated_suites) {
        self.pointInfo["Associated suites"] = props.associated_suites;
      }
      if (props.build_properties) {
        let buildProperties = props.build_properties;
        self.buildProps = buildProperties;
        if (buildProperties.hasOwnProperty("gitHubSha1s")) {
          self.pointInfo["Git commit"] = self.buildProps.gitHubSha1s.FunOS;
        }
      }
    }

    let metaData = point["metaData"];
    if (metaData.epoch) {
      let shortDate = this.commonService.getShortDateFromEpoch(metaData.epoch, this.TIMEZONE);
      self.pointInfo["Date"] = shortDate;
    }
    if (metaData.originalValue) {
      self.pointInfo["Value"] = metaData.originalValue;
    } else {
      self.pointInfo["Value"] = point["y"];
    }
  }

  fetchMetricsById(): void {
    this.setDefaults();
    this.fetchInfo();
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
  xAxisFormatter(epoch): string {
    let dateString = "Error";
    if (epoch) { //check for null values
      try {
        let pstDate = this.commonService.convertEpochToDate(epoch, this.TIMEZONE);
        let value = this.commonService.addLeadingZeroesToDate(pstDate);
        let dateStringArray = value.split(" "); // ex: dateString = (3) ["3/19/2019,", "4:49:31", "PM"]
        let dateSplits = dateStringArray[0].split("/"); //ex: dateMonth = (3) ["3", "19", "2019,"]
        dateString = dateSplits[0] + "/" + dateSplits[1]; //ex: s = "3/19"
      } catch (e) {
        this.loggerService.error("xAxis Formatter");
      }
    }
    return dateString;
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
    let s = "";
    if (x) {
      s += "<b>Date:</b> " + x + "<br>";
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
    let point = {};
    point["x"] = x;
    point["y"] = y;
    point["metaData"] = metaData;
    return point;
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

  setChartDetails(): void {
    if (this.chartInfo !== null) {
      this.previewDataSets = this.getPreviewDataSets();
      if (!this.previewDataSets) {
        this.loggerService.error("No Preview Datasets");
        return;
      }
      this.chartName = this.chartInfo.chart_name;
      this.modelName = this.chartInfo.metric_model_name;
      this.platform = this.chartInfo.platform;
      this.currentDescription = this.chartInfo.description;
      this.currentOwner = this.chartInfo.owner_info;
      this.currentSource = this.chartInfo.source;
      this.negativeGradient = !this.chartInfo.positive;
      this.leaf = this.chartInfo.leaf;
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
      } else if (this.power_category.includes(this.visualizationUnit)) {
        this.category = [...this.power_category];
      }
      this.selectedUnit = this.visualizationUnit;
    }
  }

  // populates chartInfo and fetches metrics data
  fetchInfo(): void {
    if (!this.chartInfo) {
      of (true).pipe(
        switchMap(response => {
          return this.performanceService.fetchChartInfo(this.id);
        }),
        switchMap(response => {
          this.chartInfo = response;
          this.setChartDetails();
          return of(true);
        })
      ).subscribe(response => {
        this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, this.previewDataSets);
        console.log("fetched chartInfo and fetched data");
      }, error => {
        this.loggerService.error("Unable to fetch chartInfo in fun metric");
      });
    } else {
      this.setChartDetails();
      this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, this.previewDataSets);
    }
  }

  //sets the state of the component to default values
  setDefaults(): void {
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
    payload["description"] = this.currentDescription;
    payload["owner_info"] = this.currentOwner;
    payload["source"] = this.currentSource;
    payload["negative_gradient"] = this.negativeGradient;
    payload["leaf"] = this.leaf;
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
        this.showConfigure();
      } else {
        alert("Submission failed. Please check alerts");
      }
    }, error => {
      this.loggerService.error("EditChart: Submit");
    });

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
    payload["preview_data_sets"] = previewDataSets;
    payload["metric_id"] = metricId;
    payload["count"] = this.daysInPast;
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
    let self = this;
    this.apiService.post("/metrics/data", payload).subscribe((response: any) => {
      self.allDataSets = response.data;
      if (self.allDataSets.length === 0) {
        this.values = null;
        this.status = null;
        return;
      }

      let d = new Date();
      d.setDate(d.getDate() - this.daysInPast);
      let startDate = this.commonService.convertToTimezone(d, this.TIMEZONE);

      //check if the baseline dates is later than start date then set the start date as baseline
      let baseDate = this.chartInfo.base_line_date;
      baseDate = this.commonService.convertToTimezone(baseDate, this.TIMEZONE);
      if (startDate < baseDate) {
        startDate = baseDate;
      }

      let chartDataSets = [];
      let seriesDates = [];
      this.expectedValues = [];
      this.maxDataSet = null;
      this.minDataSet = null;
      this.maxExpected = null;
      this.maxDataPoint = null;
      this.yMax = null;
      let seriesIndex = 0;
      for (let oneDataSet of self.allDataSets) {
        let outputName = this.filterDataSets[seriesIndex].output.name;
        let unit = this.filterDataSets[seriesIndex].output.unit;
        let minimum = this.filterDataSets[seriesIndex].output.min;
        let maximum = this.filterDataSets[seriesIndex].output.max;
        let expected = this.filterDataSets[seriesIndex].output.expected;
        let name = this.filterDataSets[seriesIndex].name;
        let oneChartDataArray = [];
        let lastDate = this.commonService.convertToTimezone(new Date(), this.TIMEZONE);
        let seriesDatesIndex = 0;
        while (lastDate >= startDate) {
          let valueSet = false;
          let epoch = null;
          for (let oneRecord of oneDataSet) {
            let pstDate = this.commonService.convertEpochToDate(Number(oneRecord.epoch_time), this.TIMEZONE);
            if (this.sameDay(lastDate, pstDate) && !valueSet) {
              valueSet = true;
              let outputUnit = oneRecord[outputName + "_unit"];
              let output = oneRecord[outputName];
              output = this.convertToBaseUnit(outputUnit, output);
              output = this.convertToVisualizationUnit(this.visualizationUnit, output);
              epoch = oneRecord.epoch_time;
              let metaData = {};
              metaData["epoch"] = epoch;
              if (oneRecord.hasOwnProperty("run_time_id")) {
                metaData["runTimeId"] = oneRecord.run_time_id;
              }
              let result = this.getValidatedData(output, minimum, maximum, metaData);
              oneChartDataArray.push(result);
              if (this.maxDataPoint === null) {
                this.maxDataPoint = result.y;
                this.originalMaxDataPoint = this.maxDataPoint;
              } else {
                if (result.y > this.maxDataPoint) {
                  this.maxDataPoint = result.y;
                  this.originalMaxDataPoint = this.maxDataPoint;
                }
              }
              break;
            }
          }
          if (!valueSet) {
            let metaData = {};
            metaData["epoch"] = null;
            oneChartDataArray.push(this.getValidatedData(-1, 0, -1, metaData));
          }
          if (!seriesDates[seriesDatesIndex]) {
            seriesDates[seriesDatesIndex] = this.commonService.addLeadingZeroesToDate(lastDate).substring(0, 5);
          }
          seriesDatesIndex++;
          lastDate.setDate(lastDate.getDate() - 1);
        }
        let oneChartDataSet = {name: name, data: oneChartDataArray.reverse()};
        chartDataSets.push(oneChartDataSet);
        seriesIndex++;

        //to show the expected values line and setting the max min of the chart
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
          this.maxDataSet = maximum;
        } else {
          if (maximum > this.maxDataSet) {
            this.maxDataSet = maximum;
          }
        }
        if (this.minDataSet === null && minimum > 0) {
          this.minDataSet = minimum;
        } else {
          if (minimum > 0 && minimum < this.minDataSet) {
            this.minDataSet = minimum;
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
      this.series = seriesDates.reverse();
      this.values = chartDataSets.slice();

      //set the milestones
      this.setMileStones();

      //populating data for show tables
      if (!this.minimal) {
        this.populateShowTables();
      }

      this.changeAllExpectedValues();
      this.status = null;
    }, error => {
      this.loggerService.error("fetchMetricsData");
    });
  }

  //fetching container data
  fetchContainerData(chartInfo, previewDataSets, payload): void {
    this.apiService.post('/metrics/scores', payload).subscribe((response: any) => {
      if (response.data.length === 0) {
        this.values = null;
        this.status = null;
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
      this.series = null;
      this.values = null;
      let keyList = Object.keys(response.data.scores);
      let values = [];
      let series = [];
      for (let dateTime of keyList) {
        let score = response.data.scores[dateTime].score;
        let metaData = {};
        metaData["epoch"] = dateTime;
        let result = this.getValidatedData(score, thisMinimum, thisMaximum, metaData);
        values.push(result);
        let xAxisString = this.commonService.getShortDateFromEpoch(Number(dateTime) * 1000, this.TIMEZONE);
        series.push(xAxisString);
      }
      this.values = [{data: values, name: "Scores"}];
      this.series = series;

      //setting milestone
      this.setMileStones();

      this.status = null;
    });
  }

  setMileStones(): void {
    //setting the milestones
    if (Object.keys(this.mileStoneMarkers).length > 0) {
      Object.keys(this.mileStoneMarkers).forEach((mileStone) => {
        for (let index = 0; index < this.series.length - 1; index++) {
          if ((index == 0 && this.mileStoneMarkers[mileStone] <= this.series[index])) {
            this.mileStoneIndices[mileStone] = index;
            break;
          }
          if ((this.mileStoneMarkers[mileStone] > this.series[index] && this.mileStoneMarkers[mileStone] <= this.series[index + 1])) {
            this.mileStoneIndices[mileStone] = index;
            break;
          }
        }
      });
    }
  }

  populateShowTables(): void {
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
    let index = 0;
    let self = this;
    let payload = {};
    payload["metric_id"] = this.id;
    payload["preview_data_sets"] = this.filterDataSets;
    for (let dataSet of this.allDataSets) {
      for (let rowData of dataSet) {
        let rowInTable = [];
        Object.keys(self.headers).forEach((key) => {
          if (self.isFieldRelevant(key)) {
            let value = null;
            if (key == "input_date_time") {
              // value = this.commonService.convertToTimezone(rowData[key], this.TIMEZONE);
              value = rowData["epoch_time"];
            } else {
              value = rowData[key]
            }
            rowInTable.push(value);
          }
        });
        self.data["rows"][index++] = rowInTable;
      }
    }
    self.data["totalLength"] = self.data["rows"].length;
    // this.apiService.post("/metrics/data_by_model", payload).subscribe((response) => {
    //   let dataSet = response.data;
    //   for (let rowData of dataSet) {
    //     let rowInTable = [];
    //     Object.keys(self.headers).forEach((key) => {
    //       if (self.isFieldRelevant(key)) {
    //         let value = null;
    //         if (key == "input_date_time") {
    //           // value = this.commonService.convertToTimezone(rowData[key], this.TIMEZONE);
    //           value = rowData["epoch_time"];
    //         } else {
    //           value = rowData[key]
    //         }
    //         rowInTable.push(value);
    //       }
    //     });
    //     self.data["rows"][index++] = rowInTable;
    //   }
    //   self.data["totalLength"] = self.data["rows"].length;
    // });
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
    } else if (this.power_category.includes(outputUnit)) {
      if (outputUnit === "kW") {
        output = output * Math.pow(10, 3);
      } else if (outputUnit === "MW") {
        output = output * Math.pow(10, 6);
      } else if (outputUnit === "mW") {
        output = output / Math.pow(10, 3);
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
    } else if (this.power_category.includes(outputUnit)) {
      if (outputUnit === "kW") {
        output = output / Math.pow(10, 3);
      } else if (outputUnit === "MW") {
        output = output / Math.pow(10, 6);
      } else if (outputUnit === "mW") {
        output = output * Math.pow(10, 3);
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

  //called from fetchInfo and setTimeMode
  fetchMetricsData(metricModelName, chartName, chartInfo, previewDataSets) {
    this.title = chartName;
    var self = this;
    if (!chartName) {
      return;
    }
    var self = this;
    if (this.modelName !== 'MetricContainer' && !this.minimal) {
      return this.apiService.get("/metrics/describe_table/" + this.modelName + "?get_choices=false").subscribe(function (response) {
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
  getValidatedData(data, minimum, maximum, metaData): any {
    let result = data;
    if (data < 0) {
      data = null;
    }
    result = {
      y: data,
      marker: {
        radius: 3
      },
      metaData: {}
    };
    if (metaData) {
      result.metaData = metaData;
    }
    if (data > maximum && maximum !== -1) {
      result.y = maximum;
      result.marker['symbol'] = "url(/static/media/red-x-png-7.png)";
      result.marker.radius = 3;
      result.metaData["originalValue"] = data;
    }
    return result;
  }

}
