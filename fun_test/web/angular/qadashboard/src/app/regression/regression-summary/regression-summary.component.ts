import {Component, OnInit, Input, OnChanges} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {CommonService} from "../../services/common/common.service";
import {forkJoin, from, Observable, of} from 'rxjs';
import {ReRunService} from "../re-run.service";
import {concatMap, mergeMap, switchMap} from "rxjs/operators";
import {RegressionService} from "../regression.service";


@Component({
  selector: 'app-regression-summary',
  templateUrl: './regression-summary.component.html',
  styleUrls: ['./regression-summary.component.css']
})
export class RegressionSummaryComponent implements OnInit {
  @Input() filterData: any = null;
  info = {};
  suiteExectionVersionMap = {};

  constructor(private apiService: ApiService,
              private loggerService: LoggerService,
              private commonService: CommonService,
              private reRunService: ReRunService,
              private regressionService: RegressionService) {
  }

  xValues: any [] = [];
  y1Values = [];
  detailedInfo = null;
  showDetailedInfo = false;
  public pointClickCallback: Function;
  availableModules = [];
  testCaseExecutions: any = null;
  scriptInfoMap = {};
  numBugs = 0;
  numBugsActive = 0;
  numBugsResolved = 0;
  showGlobalBugPanel = false;
  scriptSuiteBaselineMap = {};

  /*initialFilterData = [{info: "Networking overall", payload: {module: "networking"}},
    {info: "Networking sanity", payload: {module: "networking", test_case_execution_tags: ["networking-sanity"]}}
  ];*/

    initialFilterData = [{info: "Networking overall", payload: {module: "networking"}},
    {info: "Storage overall", payload: {module: "storage"}},
    {info: "Networking sanity", payload: {module: "networking", test_case_execution_tags: ["networking-sanity"]}},
    {info: "Storage sanity", payload: {module: "storage", test_case_execution_tags: ["storage-sanity"]}},
    {info: "Accelerators", payload: {test_case_execution_tags: ["palladium-apps"]}},
    {info: "Storage regression", payload: {test_case_execution_tags: ["storage-regression"]}},
    {info: "Storage performance", payload: {test_case_execution_tags: ["storage-performance"]}}
  ];


  filters = [];

  doInitializeFilters(filterData) {
    this.filters = [];
    let index = 0;
    filterData.forEach(filterDataEntry => {
      this.initializeFilter(filterDataEntry.info, filterDataEntry.payload, index);
      index++;
    });

  }
  ngOnInit() {
    this.fetchAllVersions();
    this.pointClickCallback = this.pointDetail.bind(this);
    this.setFilterData();

  }

  clickHistory(scriptPath) {
    let url = "/regression/script_history_page/" + this.scriptInfoMap[scriptPath].entry.pk;
    window.open(url, '_blank');
  }

  setFilterData() {
    let filterData = this.initialFilterData;
    if (this.filterData) {
      filterData = this.filterData;
    }
    this.doInitializeFilters(filterData);
  }

  ngOnChanges() {
    this.setFilterData();
  }

  scrollTo(elementId, index) {
    index = parseInt(index) + 1;
    this.commonService.scrollTo(elementId + index);
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
    newFilter["startDate"] = new Date(newFilter["currentDate"]);
    newFilter["currentResultsByVersion"] = {version: 0, numPassed: 0, numFailed: 0, numNotRun: 0};
    newFilter["previousResultsByVersion"] = {version: 0, numPassed: 0, numFailed: 0, numNotRun: 0};
    newFilter["currentResultsByDate"] = {date: 0, numPassed: 0, numFailed: 0, numNotRun: 0};
    newFilter["previousResultsByDate"] = {date: 0, numPassed: 0, numFailed: 0, numNotRun: 0};
    this.filters.push(newFilter);
  }

  epochMsToDate(epochTimeInMs) {
    let d = new Date(0); // The 0 there is the key, which sets the date to the epoch
    d.setUTCSeconds(epochTimeInMs / 1000);

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
      this.fetchScripts();

    }, error => {
      this.loggerService.error("/regression/get_all_versions");
    });
  }

  fetchScripts() {
    this.numBugs = 0;
    this.apiService.get("/regression/scripts").subscribe(response => {
      response.data.forEach(entry => {
        this.scriptInfoMap[entry.script_path] = {entry: entry};
        if (entry.baseline_suite_execution_id > 0) {
          let payload = {suite_execution_id: entry.baseline_suite_execution_id};
          this.apiService.post('/regression/script_execution/' + entry.pk, payload ).subscribe(response => {
            this.scriptInfoMap[entry.script_path]["baselineResults"] = response.data;
          }, error => {

          });
        }
        if (entry.bugs.length) {
          this.numBugs += entry.bugs.length;
        }
      });
      this.fetchModules();
    }, error => {
      this.loggerService.error("/regression/scripts");
    })
  }

  getBaselineResult(scriptPath, testCaseId) {
    let result = "UNKNOWN";
    if (this.scriptInfoMap.hasOwnProperty(scriptPath)) {
      if (this.scriptInfoMap[scriptPath].hasOwnProperty('baselineResults')) {
        let baselineResults = this.scriptInfoMap[scriptPath].baselineResults;
        if (baselineResults.hasOwnProperty(testCaseId)) {
          result = baselineResults[testCaseId].result;
        }
      }
    }
    return result;
  }

  matchWithBaseline(scriptPath, scriptInfo, baselineSuiteExecutionId) {
    try {
      let suiteList = Array.from(scriptInfo.suiteExecutionIdSet);
      let mostRecentSuite = Math.max.apply(Math, suiteList.map(o => o));
      let result = {matches: true, message: null};

      let baselineResults = this.scriptInfoMap[scriptPath].baselineResults;
      if (!baselineResults) {
        result.matches = false;
        result.message = "Baseline results missing for " + scriptPath;
        return result;
      }
      //console.log("Recent suite: " + mostRecentSuite);
      //console.log("Baseline results: " + baselineResults);
      let baselineResultKeys = Object.keys(baselineResults);
      let history = scriptInfo.bySuiteExecution[mostRecentSuite].history;

      if (baselineResultKeys.length !== Object.keys(history).length) {
        result.matches = false;
        result.message = "The number of test cases mismatch with the baseline";
      } else {


        for (let index = 0; index < baselineResultKeys.length; index++) {
          let baselineTestCaseId = baselineResultKeys[index];
          if (!history.hasOwnProperty(parseInt(baselineTestCaseId))) {
            let errorMessage = "Baseline TC: " + baselineTestCaseId + " not found";
            //console.log(errorMessage);
            result.matches = false;
            result.message = errorMessage;
            break;
          }
          let historyResult = history[parseInt(baselineTestCaseId)].result;
          if (historyResult !== "IN_PROGRESS") {
            if (historyResult !== baselineResults[parseInt(baselineResultKeys[index])].result) {
              let errorMessage = "Latest suite: " + mostRecentSuite + " Baseline TC: " + baselineTestCaseId + " result mismatched, baseline result: " + baselineResults[baselineResultKeys[index]].result + ", current result: " + historyResult;
              //console.log(errorMessage);
              result.matches = false;
              result.message = errorMessage;
              break;
            }
          }
        }

        //console.log(baselineResults[baselineResultKeys[index]].result);

      }
      //console.log(result);
      scriptInfo.mismatchMessage = result.message;
      return result;
    } catch (e) {
      let i = 0;
    }

  }

  prepareBucketList(index) {
    let timeBucketList = this.filters[index].timeBucketList;
    this.filters[index].timeBucketSet.forEach(element => {
      timeBucketList.push(element);
    });
    //this.timeBucketList.sort();
    try {
      let currentResultsByDate = this.filters[index].currentResultsByDate;
      currentResultsByDate.date = timeBucketList[timeBucketList.length - 1];
      let byDateTime = this.filters[index].byDateTime[currentResultsByDate.date];
      currentResultsByDate.numPassed = byDateTime.numPassed;
      currentResultsByDate.numFailed = byDateTime.numFailed;
      currentResultsByDate.numNotRun = byDateTime.numNotRun;

      let previousResultsByDate = this.filters[index].previousResultsByDate;
      previousResultsByDate.date = timeBucketList[timeBucketList.length - 2];
      byDateTime = this.filters[index].byDateTime[previousResultsByDate.date];
      previousResultsByDate.numPassed = byDateTime.numPassed;
      previousResultsByDate.numFailed = byDateTime.numFailed;
      previousResultsByDate.numNotRun = byDateTime.numNotRun;

    } catch (e) {
      let i = 0;

    }


  }

  prepareVersionList(index) {
    let versionList = this.filters[index].versionList;
    let versionSet = this.filters[index].versionSet;
    versionSet.forEach((element) => {
      versionList.push(element);
    });
    versionList.sort();
    try {
      let currentResultsByVersion = this.filters[index].currentResultsByVersion;
      currentResultsByVersion.version = versionList[versionList.length - 1];
      let bySoftwareVersion = this.filters[index].bySoftwareVersion[currentResultsByVersion.version];
      currentResultsByVersion.numPassed = bySoftwareVersion.numPassed;
      currentResultsByVersion.numFailed = bySoftwareVersion.numFailed;
      currentResultsByVersion.numNotRun = bySoftwareVersion.numNotRun;

      if (versionList.length > 1) {
        let previousResultsByVersion = this.filters[index].previousResultsByVersion;
        previousResultsByVersion.version = versionList[versionList.length - 2];
        bySoftwareVersion = this.filters[index].bySoftwareVersion[previousResultsByVersion.version];
        previousResultsByVersion.numPassed = bySoftwareVersion.numPassed;
        previousResultsByVersion.numFailed = bySoftwareVersion.numFailed;
        previousResultsByVersion.numNotRun = bySoftwareVersion.numNotRun;
      } else {
        let previousResultsByVersion = this.filters[index].previousResultsByVersion;
        previousResultsByVersion.numPassed = 0;
        previousResultsByVersion.numFailed = 0;
        previousResultsByVersion.numNotRun = 0;
      }

    } catch (e) {
      let i = 0;
    }

    let i = 0;
  }

  modeChanged() {
    this.detailedInfo = null;
  }

  scriptPathToPk(scriptPath) {
    return this.scriptInfoMap[scriptPath].entry.pk;
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

  fetchModules() {
    this.apiService.get("/regression/modules").subscribe((response) => {
      //console.log(response);
      this.availableModules = response.data;
      this.availableModules.forEach((module) => {

      });

      /*
      for (let index = 0; index < this.filters.length; index++) {
        this.fetchScriptInfo2(index).subscribe();
      }*/

      /*forkJoin(Array.from(Array(this.filters.length).keys()).map(filterIndex => {
        return this.fetchScriptInfo2(filterIndex);
      })).subscribe(() => {

      });*/
      let numbers = [];
      this.filters.map(filter => {numbers.push(numbers.length)});
        return from(numbers).pipe(
     mergeMap(filterIndex => this.fetchScriptInfo2(filterIndex))).subscribe(response => {

        }, error => {
        this.loggerService.error("Unable to fetch script info");
        });






    }, error => {
      this.loggerService.error("Error fetching modules");
    })
  }


  moreInfo(scriptInfo) {
    console.log(scriptInfo.key);
  }


  aggregateHistoryResults(historyElement) {
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


  populateResults(entry, historyInputElement) {
    let scriptDetailedInfo = entry.scriptDetailedInfo;
    let scriptPath = historyInputElement.script_path;
    if (!scriptDetailedInfo.hasOwnProperty(scriptPath)) {
      scriptDetailedInfo[scriptPath] = {bySuiteExecution: {}, suiteExecutionIdSet: new Set(), historyResults: {numPassed: 0, numFailed: 0, numNotRun: 0}};
    }
    scriptDetailedInfo[scriptPath].suiteExecutionIdSet.add(historyInputElement.suite_execution_id);

    let bySuiteExecution = scriptDetailedInfo[scriptPath].bySuiteExecution;
    if (!bySuiteExecution.hasOwnProperty(historyInputElement.suite_execution_id)) {
      bySuiteExecution[historyInputElement.suite_execution_id] = {history: {}}
    }
    bySuiteExecution[historyInputElement.suite_execution_id].history[historyInputElement.test_case_id] = (historyInputElement);

    let historyResults = this.aggregateHistoryResults(historyInputElement);
    scriptDetailedInfo[scriptPath].historyResults.numPassed += historyResults.numPassed;
    scriptDetailedInfo[scriptPath].historyResults.numFailed += historyResults.numFailed;
    scriptDetailedInfo[scriptPath].historyResults.numNotRun += historyResults.numNotRun;
    scriptDetailedInfo[scriptPath].numBugs = 0;
    scriptDetailedInfo[scriptPath].numBugsActive = 0;
    scriptDetailedInfo[scriptPath].numBugsResolved = 0;
    try {
      scriptDetailedInfo[scriptPath].numBugs = this.scriptInfoMap[scriptPath].entry.bugs.length;

    } catch (e) {
      let i = 0;
    }

    entry.numPassed += historyResults.numPassed;
    entry.numFailed += historyResults.numFailed;
    entry.numNotRun += historyResults.numNotRun;

    return historyResults;
  }

  sortSet(s) {
    return Array.from(s).sort();
  }


  getTestCaseSummary(scriptPath, testCaseId) {
    let summary = "unknown";
    if (testCaseId === 0) {
      summary = "Script setup";
    } else if (this.scriptInfoMap.hasOwnProperty(scriptPath)) {
      let testCases = this.scriptInfoMap[scriptPath].entry.test_cases;
      if (testCases.hasOwnProperty(testCaseId)) {
        summary = testCases[testCaseId].summary;
      }
    }
    return summary;
  }

  updateNumBugs(numBugs, node) {
    if (node) {
      node.numBugs = numBugs;
    } else {
      this.numBugs = numBugs;
    }
  }


  updateNumBugsActive(numBugs, node) {
    if (node) {
      node.numBugsActive = numBugs;
    } else {
      this.numBugsActive = numBugs;
    }
  }

  updateNumBugsResolved(numBugs, node) {
    if (node) {
      node.numBugsResolved = numBugs;
    } else {
      this.numBugsResolved =  numBugs;
    }
  }

  addHistoryToSoftwareVersion(index, history, softwareVersion) {
    let bySoftwareVersion = this.filters[index].bySoftwareVersion;
    let versionSet = this.filters[index].versionSet;
    if (softwareVersion.toString() === "NaN") {
      //console.log(softwareVersion);
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
    return d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate();
  }



  isGreaterThan(d1, d2) {
    if ((d1.getFullYear() > d2.getFullYear()) || ((d1.getYear() === d2.getFullYear()) && (d1.getMonth() > d2.getMonth())) || ((d1.getFullYear() === d2.getFullYear()) && (d1.getMonth() === d2.getMonth()) && (d1.getDate() > d2.getDate()))) {
      return true;
    }
    return false;
  }


  dateTimeToBucket(d) {
    //console.log(d.getYear());
    //console.log(d.getMonth());
    //console.log(d.getDate());
    //return d.getUTCMonth() + 1 + "/" + d.getUTCDate();
    return d.getMonth() + 1 + "/" + + d.getDate();
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
    if (history.execution_id === 69570) {
      let i = 0;
    }
    let currentDate = this.filters[index].currentDate;
    let today = new Date();
    let historyTime = new Date(this.regressionService.convertToLocalTimezone(history.started_time)); //.replace(/\s+/g, 'T')); // For Safari
    if (this.isGreaterThan(currentDate, historyTime)) {
      /*if (index === 4) {

        console.log("Returning:" + currentDate + "," + historyTime);
      }*/
      console.log("Check this please");
      return;
    }
    while (currentDate <= today) {
      if (this.isSameDay(currentDate, historyTime)) {
        /*
        if (index === 4) {
          console.log("Adding: " + currentDate + "," + historyTime);
        }*/
        this.addToTimeBucket(index, currentDate, history);
        break;
      }
      currentDate.setDate(currentDate.getDate() + 1);
    }
  }

  fetchScriptInfo2(index) {
    return this.apiService.post("/regression/get_test_case_executions_by_time", this.filters[index].payload).pipe(switchMap((response) => {
      this.filters[index].testCaseExecutions = response.data;
      this.filters[index].testCaseExecutions.forEach((historyElement) => {
        if (historyElement.script_path === "/networking/qos/test_cir_1.py") {
          if (historyElement.suite_execution_id === 6111)
          {
            let i = 0;
          }
        }
        //console.log(historyElement);
        if (!historyElement.is_re_run) {
          let elementSuiteExecutionId = historyElement.suite_execution_id;
          let matchingSoftwareVersion = this.suiteExectionVersionMap[elementSuiteExecutionId];
          this.addHistoryToSoftwareVersion(index, historyElement, matchingSoftwareVersion);
          this.addHistoryToDateTimeBuckets(index, historyElement);
        }

      });
      this.prepareVersionList(index);
      this.prepareBucketList(index);
      //console.log(this.filters[0]);
      this.filters[index] = {...this.filters[index]};
      return of(null);
    }))
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

  isBaselineForScript(scriptPath, suiteExecutionId) {
    let result = false;
    if (this.getBaselineSuiteExecutionId(scriptPath) === suiteExecutionId) {
        result = true;
    }
    return result;
  }

  setBaseline(detailedInfo, scriptPath, suiteExecutionId) {
    let payload = {baseline_suite_execution_id: suiteExecutionId};
    let availableSuiteExecutionId = this.getBaselineSuiteExecutionId(scriptPath);
    if (availableSuiteExecutionId === suiteExecutionId) {
      payload.baseline_suite_execution_id = null;
      suiteExecutionId = null;
    }

    this.apiService.post("/regression/script_update/" + this.scriptInfoMap[scriptPath].entry.pk, payload).subscribe(response => {
      this.scriptInfoMap[scriptPath].entry.baseline_suite_execution_id = suiteExecutionId;
      //detailedInfo = {...detailedInfo};
      window.location.reload();
    });
  }


  getBaselineSuiteExecutionId(scriptPath) {
    let result = null;
    if (this.scriptInfoMap.hasOwnProperty(scriptPath)) {
      result = this.scriptInfoMap[scriptPath].entry.baseline_suite_execution_id;
      if (result < 0) {
        result = null;
      }

    }
    return result;
  }

  /*
  getBaselineSuiteExecutionId(scriptPath) {
    return of(67).pipe(delay(2000));
    /*let result = null;
    if (this.scriptInfoMap.hasOwnProperty(scriptPath)) {
      result = this.scriptInfoMap[scriptPath].baseline_suite_execution_id;
      if (result < 0) {
        result = null;
      }
    }
    return result;

  }
  */



}
