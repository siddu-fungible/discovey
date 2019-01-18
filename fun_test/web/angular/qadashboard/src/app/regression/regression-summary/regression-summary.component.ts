import { Component, OnInit } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {CommonService} from "../../services/common/common.service";
import {el} from "@angular/platform-browser/testing/src/browser_util";

@Component({
  selector: 'app-regression-summary',
  templateUrl: './regression-summary.component.html',
  styleUrls: ['./regression-summary.component.css']
})
export class RegressionSummaryComponent implements OnInit {
  info = {};
  suiteExectionVersionMap = {};
  constructor(private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService) { }
  xValues: any [] = [];
  y1Values = [];
  detailedInfo = null;
  showDetailedInfo = false;
  public pointClickCallback: Function;
  availableModules = [];
  testCaseExecutions: any = null;

  //bySoftwareVersion: any = {};

  /*
  filters = [
    {info: "Networking", payload: {module: "networking"}, testCaseExecutions: null, bySoftwareVersion: {}, metadata: {index: 0}, byDateTime: {}},
    {info: "Storage", payload: {module: "storage"}, testCaseExecutions: null, bySoftwareVersion: {}, metadata: {index: 1}, byDateTime: {}}
  ];*/

  filters = [
  ];

  ngOnInit() {
    this.fetchAllVersions();
    this.pointClickCallback = this.pointDetail.bind(this);
    this.initializeFilter("Networking", {module: "networking"}, 0);
    this.initializeFilter("Storage", {module: "storage"}, 1);
    let i = 0;

  }

  initializeFilter(info, payload, index) {
    let newFilter = {};
    newFilter["info"] = info;
    newFilter["payload"] = payload;
    newFilter["testCaseExecutions"] = null;
    newFilter["bySoftwareVersion"] = {};
    newFilter["metadata"] = {index: index};
    newFilter["byDateTime"] = {};
    newFilter["versionList"] = [];
    newFilter["versionSet"] = new Set();
    newFilter["timeBucketList"] = [];
    newFilter["timeBucketSet"] = new Set();
    newFilter["currentDate"] = new Date(2018, 11, 1, 0, 1);
    newFilter["startDate"] =  new Date(newFilter["currentDate"]);
    this.filters.push(newFilter);
  }

  epochMsToDate(epochTimeInMs) {
    let d = new Date(0); // The 0 there is the key, which sets the date to the epoch
    d.setUTCSeconds(epochTimeInMs/ 1000);

    return d.toLocaleString();
  }

  fetchAllVersions() {
    this.apiService.get("/regression/get_all_versions").subscribe((response) => {
      let entries = response.data;
      entries.forEach((entry) => {
        let version = parseInt(entry.version);
        //this.versionSet.add(version);
        this.suiteExectionVersionMap[entry.execution_id] = version;

      });
      this.fetchModules();

    }, error => {
      this.loggerService.error("/regression/get_all_versions");
    });

  }

  prepareBucketList(index) {
    let timeBucketList = this.filters[index].timeBucketList;
    this.filters[index].timeBucketSet.forEach(element => {
      timeBucketList.push(element);
    });
    //this.timeBucketList.sort();
  }

  prepareVersionList(index) {
    let versionList = this.filters[index].versionList;
    let versionSet = this.filters[index].versionSet;
    versionSet.forEach((element) => {
      versionList.push(element);
      });
    versionList.sort();
  }

  modeChanged() {
    this.detailedInfo = null;
  }

  showPointDetails(pointInfo): void {
    let metadata = pointInfo.metadata;
    let index = metadata.index;
    let mode = metadata.mode;
    let resultType = pointInfo.name;
    let category = pointInfo.category;

    if (mode === "version") {
      this.detailedInfo = this.filters[index].bySoftwareVersion[category];
    }
    if (mode === "date") {
      this.detailedInfo = this.filters[index].byDateTime[category];
    }
    this.detailedInfo.mode = mode;
    this.detailedInfo.category = category;
    this.showDetailedInfo = true;
    this.commonService.scrollTo('detailed-info');
    let i = 0;

  }

  pointDetail(x, y, name): any {
    let moduleInfo = this.info[x];
    return "xx";
  }

  fetchModules () {
    this.apiService.get("/regression/modules").subscribe((response) => {
      //console.log(response);
      this.availableModules = response.data;
      this.availableModules.forEach((module) => {

      });
      for (let index = 0; index < this.filters.length; index++) {
        this.fetchScriptInfo2(index);
      }

    }, error => {
      this.loggerService.error("Error fetching modules");
    })
  }

  prepareBySoftwareVersion(index) {
    this.filters[index].versionList.forEach((softwareVersion) => {
      for (let index = 0; index < this.filters.length; index++) {
        if (Number.isNaN(softwareVersion)) {
          //console.log(softwareVersion);
          continue;
        }

        this.filters[index].bySoftwareVersion[softwareVersion] = {
          scriptDetailedInfo: {showingDetails: false},
          numPassed: 0,
          numFailed: 0,
          numNotRun: 0
        };
      }
    })
  }

  moreInfo(scriptInfo) {
    console.log(scriptInfo.key);
  }


  aggregateHistoryResults (historyElement) {
    let result = {numPassed: 0, numFailed: 0, numNotRun: 0};
    if (historyElement.result === "PASSED") {
      result.numPassed += 1;

    } else if (historyElement.result === "FAILED") {
      result.numFailed += 1;

    } else if (historyElement.result === "NOT_RUN") {
      result.numNotRun += 1;
    }
    return result;
  }


  populateResults(entry, history) {
    let scriptDetailedInfo = entry.scriptDetailedInfo;
    let scriptPath = history.script_path;
    if (!scriptDetailedInfo.hasOwnProperty(scriptPath)) {
      scriptDetailedInfo[scriptPath] = {history: [], historyResults: {numPassed: 0, numFailed: 0, numNotRun: 0}};
    }
    scriptDetailedInfo[scriptPath].history.push(history);
    let historyResults = this.aggregateHistoryResults(history);
    scriptDetailedInfo[scriptPath].historyResults.numPassed += historyResults.numPassed;
    scriptDetailedInfo[scriptPath].historyResults.numFailed += historyResults.numFailed;
    scriptDetailedInfo[scriptPath].historyResults.numNotRun += historyResults.numNotRun;

    entry.numPassed += historyResults.numPassed;
    entry.numFailed += historyResults.numFailed;
    entry.numNotRun += historyResults.numNotRun;
    return historyResults;
  }


  addHistoryToSoftwareVersion(index, history, softwareVersion) {
    let bySoftwareVersion = this.filters[index].bySoftwareVersion;
    let versionSet = this.filters[index].versionSet;
    if (softwareVersion.toString() === "NaN") {
      console.log(softwareVersion);
      return;
    }
    versionSet.add(softwareVersion);
    let scriptPath = history.script_path;
    if (!bySoftwareVersion.hasOwnProperty(softwareVersion)) {
      bySoftwareVersion[softwareVersion] = {
          scriptDetailedInfo: {showingDetails: false},
          numPassed: 0,
          numFailed: 0,
          numNotRun: 0
        };
    }
    let softwareVersionEntry = bySoftwareVersion[softwareVersion];
    let historyResults = this.populateResults(softwareVersionEntry, history);
  }

  isSameDay(d1, d2) {
    return d1.getUTCFullYear() === d2.getUTCFullYear() &&
      d1.getUTCMonth() === d2.getUTCMonth() &&
      d1.getUTCDate() === d2.getUTCDate();
  }

  isSameDay2(d1, d2) {
    console.log(d1.getUTCFullYear(), d2.getUTCFullYear());
    console.log(d1.getUTCMonth(), d2.getUTCMonth());
    console.log(d1.getUTCDate(), d2.getUTCDate());
  }


  dateTimeToBucket(d) {
    //console.log(d.getYear());
    //console.log(d.getMonth());
    //console.log(d.getDate());
    return d.getMonth() + 1 + "/" + d.getDate();
  }

  addToTimeBucket(index, d, history) {
    let timeBucketSet = this.filters[index].timeBucketSet;
    let timeBucket = this.dateTimeToBucket(d);
    //console.log("Time bucket:" + "," + d + "," + timeBucket);
    let byDateTime = this.filters[index].byDateTime;
    if (!this.filters[index].byDateTime.hasOwnProperty(timeBucket)) {
      byDateTime[timeBucket] = {
          scriptDetailedInfo: {showingDetails: false},
          numPassed: 0,
          numFailed: 0,
          numNotRun: 0
        };
    }
    let scriptDetailedInfo = byDateTime[timeBucket].scriptDetailedInfo;
    let dateTimeBucketEntry = byDateTime[timeBucket];
    let historyResults = this.populateResults(dateTimeBucketEntry, history);
    //console.log("Addtotimebucket: " + index);
    timeBucketSet.add(timeBucket);
  }

  addHistoryToDateTimeBuckets(index, history) {
    let currentDate = this.filters[index].currentDate;
    //console.log("AddHistory: " + index);
    let today = new Date();
    //console.log(today);
    let historyTime = new Date(history.started_time);
    //console.log(historyTime);
    if (index === 1) {
      let o = 0;
    }
    if (currentDate > historyTime) {
      return;
    }
    while (currentDate <= today) {
      //console.log("comparing: " + this.currentDate + "," + historyTime);
      if (this.isSameDay(currentDate, historyTime)) {
        //console.log("Found match, " + this.currentDate + "," + historyTime);
        //this.isSameDay2(this.currentDate, historyTime);
        this.addToTimeBucket(index, currentDate, history);
        break;
      }
      currentDate.setDate(currentDate.getDate() + 1);
    }
    let i = 0;
  }

  fetchScriptInfo2(index) {
    this.apiService.post("/regression/get_test_case_executions_by_time", this.filters[index].payload).subscribe((response) => {
      this.filters[index].testCaseExecutions = response.data;
      this.filters[index].testCaseExecutions.forEach((historyElement) => {
        //console.log(historyElement);
        let elementSuiteExecutionId = historyElement.suite_execution_id;
        let matchingSoftwareVersion = this.suiteExectionVersionMap[elementSuiteExecutionId];
        this.addHistoryToSoftwareVersion(index, historyElement, matchingSoftwareVersion);
        this.addHistoryToDateTimeBuckets(index, historyElement);
      });
      this.prepareVersionList(index);
      this.prepareBucketList(index);
      let i = 0;
      this.filters[index] = {...this.filters[index]};
    }, error => {
    })
  }


  getMatchingModule(moduleName) {
    let matchedModule = null;
    for (let i = 0; i < this.availableModules.length; i++) {
      let availableModule = this.availableModules[i];
      if (availableModule.name === moduleName) {
       matchedModule = availableModule;
      }
    }
    return matchedModule;
  }


  getKeys(map) {
    //console.log(map.keys());
    try {
      let a = Array.from(Object.keys(map));
      return a;
    } catch (e) {
      console.log(e);
    }


  }

  p(s) {
    let i = 0;
  }

  test() {
    console.log(this.info);
    console.log(this.info["storage"].detailedInfo.scriptDetailedInfo);
  }

  public functionCalledOnEachIteration(index, item) {
    debugger;
    console.log('trackByFn', index, item);
    return item;
  }

  getTestCaseExecutions(index) {
    return this.filters[index].testCaseExecutions;
  }

}


