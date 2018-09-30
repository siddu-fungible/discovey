import {Component, OnInit, Input} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {Observable} from "rxjs";

@Component({
  selector: 'fun-metric-chart',
  templateUrl: './fun-metric-chart.component.html',
  styleUrls: ['./fun-metric-chart.component.css']
})
export class FunMetricChartComponent implements OnInit {
  status: any;
  showingTable: boolean;
  chartInfo: any;
  @Input() chartName: any;
  @Input() modelName: any;
  headers: any;
  allData: any;
  metricId: any;
  editingDescription: boolean = false;
  inner: any = {};
  atomic: boolean = false;
  previewDataSets: any = null;
  currentDescription: any;
  waitTime: number = 0;
  values: any;
  charting: any;
  width: any;
  height: any;
  pointClickCallback: any = null;
  tableInfo: any;
  buildInfo: any;
  timeMode: string;
  negativeGradient: boolean;
  leaf: boolean;
  title: any;
  series: any;
  filterDataSets: any;

  yValues: any = [];
  xValues: any = [];
  chartTitle: string;
  xAxisLabel: string;
  yAxisLabel: string;

  chart1XaxisTitle: any;
  chart1YaxisTitle: any;
  y1AxisTitle: any;
  public formatter: Function;
  public tooltip: Function;


  constructor(private apiService: ApiService, private loggerService: LoggerService) {
  }

  ngOnInit() {

    this.yValues.push({name: 'series 1', data: [1, 2, 3, 4, 5]});
    this.yValues.push({name: 'series 2', data: [6, 7, 8, 9, 10]});
    this.yValues.push({name: 'series 3', data: [11, 12, 13, 14, 15]});
    this.yValues.push({name: 'series 4', data: [16, 17, 18, 19, 20]});
    this.yValues.push({name: 'series 5', data: [21, 22, 23, 24, 25]});
    this.xValues.push([0, 1, 2, 3, 4]);
    this.chartTitle = "Funchart";
    this.xAxisLabel = "Date";
    this.yAxisLabel = "Range";

    this.status = "idle";
    this.showingTable = false;
    this.setDefault();
    this.headers = null;
    this.metricId = -1;
    this.editingDescription = false;
    this.inner = {};
    this.inner.currentDescription = "TBD";
    this.currentDescription = "---";


    if (this.chartName) {
      this.fetchInfo();
    }

    this.values = null;
    this.charting = true;
    this.buildInfo = null;
    this.fetchBuildInfo();
    this.formatter = this.xAxisFormatter.bind(this);
    this.tooltip = this.tooltipFormatter.bind(this);
    // if (this.pointClickCallback) {
    //   this.pointClickCallback = (point) => {
    //     if (!$attrs.pointClickCallback) return null;
    //     this.pointClickCallback()(point);
    //   };
    // }

  }

  ngOnChanges() {
    this.setDefault();
    this.fetchInfo();
  }

   public xAxisFormatter(value): any {
      let s = "Error";
      const monthNames = ["null", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      let r = /(\d{4})-(\d{2})-(\d{2})/g;
      let match = r.exec(value);

      if (this.timeMode === "month") {
        if (match) {
          let month = parseInt(match[2]);
          s = monthNames[month];
        }
      }
      else {
        if (match) {
          s = match[2] + "/" + match[3];
        }
      }
      return s;

    }

    tooltipFormatter(x, y): any {
      let softwareDate = "Unknown";
      let hardwareVersion = "Unknown";
      let sdkBranch = "Unknown";
      let gitCommit = "Unknown";
      let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
      let match = r.exec(x);
      let key = "";
      if (match) {
        key = match[1];
      }
      else {
        let reg = /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})/g;
        match = reg.exec(x);
        if (match) {
          key = match[1].replace('T', ' ');
        }
      }
      let s = "Error";

      if (this.buildInfo && key in this.buildInfo) {
        softwareDate = this.buildInfo[key]["software_date"];
        hardwareVersion = this.buildInfo[key]["hardware_version"];
        sdkBranch = this.buildInfo[key]["fun_sdk_branch"];
        s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
        s += "<b>Software date:</b> " + softwareDate + "<br>";
        s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
        s += "<b>Git commit:</b> " + this.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "") + "<br>";
        s += "<b>Value:</b> " + y + "<br>";
      } else {
        s = "<b>Value:</b> " + y + "<br>";
      }

      return s;
    }

  fetchInfo() {
    let payload = {};
    payload["metric_model_name"] = this.modelName;
    payload["chart_name"] = this.chartName;

    this.apiService.post("/metrics/chart_info", payload).subscribe((response) => {
      this.chartInfo = response.data;
      if (this.chartInfo !== null) {
        this.previewDataSets = this.chartInfo.data_sets;
        this.currentDescription = this.chartInfo.description;
        this.inner.currentDescription = this.currentDescription;
        this.negativeGradient = !this.chartInfo.positive;
        this.inner.negativeGradient = this.negativeGradient;
        this.leaf = this.chartInfo.leaf;
        this.inner.leaf = this.leaf;
        this.status = "idle";
      }
      setTimeout(() => {
        this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, null);
      }, this.waitTime);
    }, error => {
      this.loggerService.error("fun_metric_chart: chart_info");
    });

  }

  setDefault(): void {
    this.timeMode = "all";
  }

  toggleEdit() {
    this.editingDescription = !this.editingDescription;
  }

  changeClass(divId, buttonId): void {
    let divIdClass = window.document.querySelector(divId);
    divIdClass.removeClass('in');
    let collapseArrow = window.document.querySelector(buttonId);
    collapseArrow.addClass('collapsed');
  }

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

  submit(): void {
    //this.previewDataSets = this.copyChartInfo.data_sets;
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

  fetchChartInfo(): any {
    let payload = {};
    payload["metric_model_name"] = this.modelName;
    payload["chart_name"] = this.chartName;

    if (!this.chartInfo) {
      return this.apiService.post("/metrics/chart_info", payload).subscribe((chartInfo) => {
        this.chartInfo = chartInfo;
        if (this.chartInfo !== null) {
          this.previewDataSets = this.chartInfo.data_sets;
          this.currentDescription = this.chartInfo.description;
          this.inner.currentDescription = this.currentDescription;
          this.negativeGradient = !this.chartInfo.positive;
          this.inner.negativeGradient = this.negativeGradient;
          this.leaf = this.chartInfo.leaf;
          this.inner.leaf = this.leaf;
          this.status = "idle";
        }
        return this.chartInfo;
      }, error => {
        this.loggerService.error("fun_metric_chart: chart_info");
      });
    } else {
      return this.chartInfo;
    }

  }

  fetchBuildInfo(): void {
    this.apiService.get('/regression/jenkins_job_id_maps').subscribe((data) => {
      this.apiService.get('/regression/build_to_date_map').subscribe((data) => {
        this.buildInfo = data;
      }, error => {
        this.loggerService.error("regression/build_to_date_map");
      });
    }, error => {
      this.loggerService.error("fetchBuildInfo");
    });
  }

  showTables(): void {
    this.showingTable = !this.showingTable;
  }

  setTimeMode(mode): void {
    this.timeMode = mode;
    if (this.chartInfo) {
      this.fetchMetricsData(this.modelName, this.chartName, this.chartInfo, this.previewDataSets); // TODO: Race condition on chartInfo
    } else {
      this.fetchMetricsData(this.modelName, this.chartName, null, this.previewDataSets); // TODO: Race condition on chartInfo
    }
  }

  getDatesByTimeMode(dateList) {
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
    }
    else if (this.timeMode === "month") {
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
    }
    else {
      for (let i = len - 1; i >= 0; i--) {
        filteredDate.push([i, i]);
      }
      result = filteredDate.reverse();
    }
    return result;
  }

  shortenKeyList(keyList: any) {
    let newList = [];
    for (let key of keyList) {
      let r = /(\d{4})-(\d{2})-(\d{2})/g;
      let match = r.exec(key);
      let s = match[2] + "/" + match[3];
      newList.push(s)
    }
    return newList;
  }

  fixMissingDates(dates) {
    let firstString = dates[0].replace(/\s+/g, 'T');
    //firstString = firstString.replace('+', 'Z');
    //firstString = firstString.substring(0, firstString.indexOf('Z'));
    let firstDate = new Date(firstString);
    let today = new Date();
    let yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    yesterday.setHours(23, 59, 59);
    let lastDate = yesterday;

    let currentDate = firstDate;
    let datesIndex = 0;
    let finalDates = [];
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
    let j = 0;
    return finalDates;
  }

  sameDay(d1, d2) {
    return d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate();
  }

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
      this.status = "idle";
      this.tableInfo = tableInfo;

      let filterDataSets = [];
      if (previewDataSets) {
        filterDataSets = previewDataSets;
      } else {
        //console.log("Chart Info:" + chartInfo);
        if (chartInfo) {
          filterDataSets = chartInfo['data_sets'];
          //console.log("C DS:" + chartInfo.data_sets);
        }
      }
      this.filterDataSets = filterDataSets;

      this.status = "Fetch data";

      this.apiService.post("/metrics/data", payload).subscribe((response: any) => {
        let allDataSets = response.data;
        self.status = "idle";
        if (allDataSets.length === 0) {
          this.values = null;
          return;
        }

        let keySet = new Set();
        /*
        let firstDataSet = allDataSets[0];
        firstDataSet.forEach((oneRecord) => {
            keySet.add(oneRecord.input_date_time.toString());
        });*/
        for (let oneDataSet of allDataSets) {
          for (let oneRecord of oneDataSet) {
            keySet.add(oneRecord.input_date_time.toString());
          }
        }
        // allDataSets.foreach((oneDataSet) => {
        //   oneDataSet.foreach((oneRecord) => {
        //     keySet.add(oneRecord.input_date_time.toString());
        //   });
        // });

        let keyList = Array.from(keySet);
        keyList.sort();
        this.shortenKeyList(keyList);
        keyList = this.fixMissingDates(keyList);
        let originalKeyList = keyList;
        keyList = this.getDatesByTimeMode(keyList);

        let chartDataSets = [];
        let seriesDates = [];
        let dataSetIndex = 0;

        this.allData = allDataSets;
        this.status = "Preparing chart data-sets";
        for (let oneDataSet of allDataSets) {

          let oneChartDataArray = [];
          for (let i = 0; i < keyList.length; i++) {
            let output = null;
            let total = 0;
            let count = 0;
            let matchingDateFound = false;
            seriesDates.push(originalKeyList[keyList[i][0]]);
            let startIndex = keyList[i][0];
            let endIndex = keyList[i][1];
            while (startIndex >= endIndex) {
              for (let j = 0; j < oneDataSet.length; j++) {
                let oneRecord = oneDataSet[j];
                if (oneRecord.input_date_time.toString() === originalKeyList[startIndex]) {
                  matchingDateFound = true;
                  let outputName = this.filterDataSets[dataSetIndex].output.name;
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
              }
              startIndex--;
            }
            if (count !== 0) {
              output = total / count;
            }
            let thisMinimum = this.filterDataSets[dataSetIndex].output.min;
            let thisMaximum = this.filterDataSets[dataSetIndex].output.max;
            oneChartDataArray.push(this.getValidatedData(output, thisMinimum, thisMaximum));
          }
          let oneChartDataSet = {name: this.filterDataSets[dataSetIndex].name, data: oneChartDataArray};
          chartDataSets.push(oneChartDataSet);
          dataSetIndex++;
        }

        this.status = "idle";
        this.series = seriesDates;
        this.values = chartDataSets;
        this.headers = this.tableInfo;
      }, error => {
        this.loggerService.error("fetchMetricsData");
      });
    }
    else {
      this.status = "Fetch data";
      console.log("Fetch Scores");
      this.apiService.post('/metrics/scores', payload).subscribe((response: any) => {
        self.status = "idle";
        if (response.data.length === 0) {
          this.values = null;
          return;
        }

        let values = [];
        let series = [];
        let keyList = Object.keys(response.data.scores);
        keyList.sort();
        for (let dateTime of keyList) {
          //values.push(data.scores[dateTime].score);
          let d = new Date(1000 * Number(dateTime)).toISOString();
          //let dateSeries = d.setUTCSeconds(dateTime);
          series.push(d);
        }

        this.shortenKeyList(series);
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
            while (startIndex >= endIndex) {
              for (let j = 0; j < keyList.length; j++) {
                let dateTime: any = keyList[j];
                let d = new Date(dateTime * 1000).toISOString();
                if (d === series[startIndex]) {
                  total += response.data.scores[dateTime].score;
                  count++;
                }
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
          this.values = [{data: values}];
          this.series = dateSeries;
          this.status = "idle";
          //let keyList = Array.from(keySet);
        }
      });
    }
  }

  fetchMetricsData(metricModelName, chartName, chartInfo, previewDataSets) {
    this.title = chartName;
    var self = this;
    if (!chartName) {
      return;
    }
    var self = this;
    if (!this.tableInfo && metricModelName !== 'MetricContainer') {
      return this.apiService.get("/metrics/describe_table/" + metricModelName).subscribe(function (response) {
        //console.log("FunMetric: Describe table: " + metricModelName);
        self.tableInfo = response.data;
        // return self.tableInfo;
        self.fetchData(metricModelName, chartName, chartInfo, previewDataSets, self.tableInfo);
      }, error => {
        this.loggerService.error("fetchMetricsData");
      })
    } else {
      // return this.tableInfo;
      this.fetchData(metricModelName, chartName, chartInfo, previewDataSets, this.tableInfo);
    }
  }

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

  counter(num: number): number[] {
    let newArray = new Array(num);
    return newArray;
  }


}
