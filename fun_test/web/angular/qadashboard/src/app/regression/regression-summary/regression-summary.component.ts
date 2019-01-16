import { Component, OnInit } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {CommonService} from "../../services/common/common.service";

@Component({
  selector: 'app-regression-summary',
  templateUrl: './regression-summary.component.html',
  styleUrls: ['./regression-summary.component.css']
})
export class RegressionSummaryComponent implements OnInit {
  info = {};
  versionSet = new Set(); // The set of all software versions
  versionMap = {};
  versionList = [];
  suiteExectionVersionMap = {};
  constructor(private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService) { }
  xValues: any [] = [];
  y1Values = [];
  detailedInfo = null;
  showDetailedInfo = false;
  public pointClickCallback: Function;
  allRegressionScripts = [];
  dropdownSettings = {};
  selectedModules: any[] = [];
  availableModules = [];
  testCaseExecutions: any = null;
  //bySoftwareVersion: any = {};

  filters = [
    {info: "Networking", payload: {module: "networking"}, testCaseExecutions: null, bySoftwareVersion: {}, metadata: {index: 0}},
    {info: "Storage", payload: {module: "storage"}, testCaseExecutions: null, bySoftwareVersion: {}, metadata: {index: 1}}
  ];


  ngOnInit() {
    this.dropdownSettings = {
      singleSelection: false,
      idField: 'name',
      textField: 'verbose_name',
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      itemsShowLimit: 3,
      allowSearchFilter: true
    };
    this.fetchAllVersions();
    /*
    this.y1Values = [{
        name: 'Passed',
        data: []
    }, {
        name: 'Failed',
        data: []
    }, {
        name: 'Not-run',
        data: []
    }]*/
    this.pointClickCallback = this.pointDetail.bind(this);

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
        this.versionSet.add(version);
        this.versionMap[version] = entry;
        this.suiteExectionVersionMap[entry.execution_id] = version;

      });
      //console.log(this.versionSet);
      if (this.versionSet.size > 0) {
        this.versionSet.forEach((element) => {
          this.versionList.push(element);
        });
        this.versionList.sort();
        this.prepareBySoftwareVersion();
        //this.xValues = this.versionList;
        this.fetchModules();
      }

    }, error => {
      this.loggerService.error("/regression/get_all_versions");
    });

  }

  showPointDetails(pointInfo): void {
    //let moduleInfo = this.infobySoftwareVersion[pointInfo.category];
    let metadata = pointInfo.metadata;
    let index = metadata.index;
    let resultType = pointInfo.name;
    let category = pointInfo.category;

    this.detailedInfo = this.filters[index].bySoftwareVersion[category];
    this.detailedInfo.softwareVersion = category;
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
        for (let index = 0; index < this.filters.length; index++) {
          this.fetchScriptInfo2(index);
        }

      });
    }, error => {
      this.loggerService.error("Error fetching modules");
    })
  }

  prepareBySoftwareVersion() {
    this.versionList.forEach((softwareVersion) => {

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

  modifyScriptAllocationClick (moduleInfo) {
    moduleInfo.modifyingScriptAllocation = !moduleInfo.modifyingScriptAllocation;
    this.fetchRegressionScripts();
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

  parseHistory2(index, history, softwareVersion) {
    let bySoftwareVersion = this.filters[index].bySoftwareVersion;
    if (softwareVersion.toString() === "NaN") {
      console.log(softwareVersion);
      return;
    }
    //console.log(softwareVersion);
    //let bySoftwareVersion = this.bySoftwareVersion;
    let scriptPath = history.script_path;
    if (bySoftwareVersion.hasOwnProperty(softwareVersion)) {
      let softwareVersionEntry = bySoftwareVersion[softwareVersion];
      let scriptDetailedInfo = softwareVersionEntry.scriptDetailedInfo;
      if (!scriptDetailedInfo.hasOwnProperty(scriptPath)) {
        scriptDetailedInfo[scriptPath] = {history: [], historyResults: {numPassed: 0, numFailed: 0, numNotRun: 0}};
      }
      scriptDetailedInfo[scriptPath].history.push(history);
      let historyResults = this.aggregateHistoryResults(history);
      scriptDetailedInfo[scriptPath].historyResults.numPassed += historyResults.numPassed;
      scriptDetailedInfo[scriptPath].historyResults.numFailed += historyResults.numFailed;
      scriptDetailedInfo[scriptPath].historyResults.numNotRun += historyResults.numNotRun;

      softwareVersionEntry.numPassed += historyResults.numPassed;
      softwareVersionEntry.numFailed += historyResults.numFailed;
      softwareVersionEntry.numNotRun += historyResults.numNotRun;
    } else {
      let i = 0;
    }
  }

  fetchScriptInfo2(index) {
    this.apiService.post("/regression/get_test_case_executions_by_time", this.filters[index].payload).subscribe((response) => {
      this.filters[index].testCaseExecutions = response.data;
      this.filters[index].testCaseExecutions.forEach((historyElement) => {
        //console.log(historyElement);
        let elementSuiteExecutionId = historyElement.suite_execution_id;
        let matchingSoftwareVersion = this.suiteExectionVersionMap[elementSuiteExecutionId];
        this.parseHistory2(index, historyElement, matchingSoftwareVersion);
      });
      let i = 0;
    }, error => {
    })
  }

  fetchRegressionScripts() {
    this.apiService.get("/regression/scripts").subscribe((response) => {
      this.allRegressionScripts = response.data;
      // Set selected modules for each script
      this.allRegressionScripts.forEach((regressionScript) => {
        regressionScript["selectedModules"] = [];
        regressionScript["savedSelectedModules"] = [];
        regressionScript["dirty"] = false;
        regressionScript.modules.forEach((module) => {
          regressionScript.selectedModules.push(this.getMatchingModule(module));
        });
        regressionScript.savedSelectedModules = [...regressionScript.selectedModules];
      });
    }, error => {
      this.loggerService.error("/regression/scripts");
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

  submitSelectModuleClick(regressionScript) {
    console.log(regressionScript.selectedModules);
    let payload = {script_path: regressionScript.script_path, modules: regressionScript.selectedModules};
    this.apiService.post("/regression/script", payload).subscribe((response) => {
      regressionScript.dirty = false;
      regressionScript.savedSelectedModules = [...regressionScript.selectedModules];
    }, error => {
      this.loggerService.error("/regression/script");
      this.dismissSelectModuleClick(regressionScript);
    })
  }

  dismissSelectModuleClick(regressionScript) {
    regressionScript.selectedModules = [...regressionScript.savedSelectedModules];
    regressionScript.dirty = false;
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

  prepareValuesForChart(moduleInfo) {
    console.log("Prepare values for chart");
    let i = 0;
    //console.log(this.xValues);
    Object.keys(moduleInfo.bySoftwareVersion).forEach((softwareVersion) => {
      let intSoftwareVersion = parseInt(softwareVersion);
      let numPassed = moduleInfo.bySoftwareVersion[intSoftwareVersion].numPassed;
      let numFailed = moduleInfo.bySoftwareVersion[intSoftwareVersion].numFailed;
      let numNotRun = moduleInfo.bySoftwareVersion[intSoftwareVersion].numNotRun;
      let total = numPassed + numFailed + numNotRun;
      if (total) {
        moduleInfo.xValues.push(intSoftwareVersion);
        moduleInfo.y1Values[0].data.push(numPassed);
        moduleInfo.y1Values[1].data.push(numFailed);
        moduleInfo.y1Values[2].data.push(numNotRun);
        moduleInfo.xValues = [...moduleInfo.xValues];
        moduleInfo.y1Values = [...moduleInfo.y1Values];
      }


    });
    //console.log(this.xValues);
    for (let index = 0; index < this.filters.length; index++) {
      this.fetchScriptInfo2(index);
    };
    this.filters = [...this.filters];


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


