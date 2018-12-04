import { Component, OnInit } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {CommonService} from "../../services/common/common.service";

@Component({
  selector: 'app-regression-admin',
  templateUrl: './regression-admin.component.html',
  styleUrls: ['./regression-admin.component.css']
})
export class RegressionAdminComponent implements OnInit {
  info = {};
  versionSet = new Set(); // The set of all software versions
  versionList = [];
  suiteExectionVersionMap = {};
  constructor(private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService) { }
  xValues: any [] = [];
  y1Values = [];
  detailedInfo = null;
  showDetailedInfo = false;
  public pointClickCallback: Function;
  allRegressionScripts = [];
  unallocatedRegressionScripts = [];
  dropdownSettings = {};
  selectedModules: any[] = [];
  availableModules = [];
  modifyingScriptAllocation = null;


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
    //this.fetchRegressionScripts();

  }

  fetchAllVersions() {
    this.apiService.get("/regression/get_all_versions").subscribe((response) => {
      let entries = response.data;
      entries.forEach((entry) => {
        let version = parseInt(entry.version);
        this.versionSet.add(version);
        this.suiteExectionVersionMap[entry.execution_id] = version;

      });
      console.log(this.versionSet);
      if (this.versionSet.size > 0) {
        this.versionSet.forEach((element) => {
          this.versionList.push(element);
        });
        this.versionList.sort();
        //this.xValues = this.versionList;
        this.fetchModules();
      }

    }, error => {
      this.loggerService.error("/regression/get_all_versions");
    });

  }

  showPointDetails(pointInfo): void {
    //let moduleInfo = this.infobySoftwareVersion[pointInfo.category];
    let moduleName = pointInfo.metadata.module;
    let resultType = pointInfo.name;
    let softwareVersion = pointInfo.category;
    let moduleInfo = this.info[moduleName];
    this.detailedInfo = moduleInfo.bySoftwareVersion[softwareVersion];
    this.detailedInfo["softwareVersion"] = softwareVersion;
    //console.log(moduleInfo.detailedInfo.scriptDetailedInfo);
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
      console.log(response);
      this.availableModules = response.data;
      this.availableModules.forEach((module) => {
        this.info[module.name] = {name: module.name, verboseName: module.verbose_name};
        this.fetchRegressionScripts();
        this.preparePlaceHolders(module.name, this.info[module.name]);
        this.fetchScriptInfo(module.name, this.info[module.name]);
      });
    }, error => {
      this.loggerService.error("Error fetching modules");
    })
  }

  preparePlaceHolders (moduleName, moduleInfo) {
    // create a bySoftwareVersion key under each module
    // byVersion is an array of software versions
    moduleInfo["y1Values"] = [{
        name: 'Passed',
        data: [],
        color: 'green',
        metadata: {module: moduleName}
    }, {
        name: 'Failed',
        data: [],
        color: 'red',
        metadata: {module: moduleName}

    }, {
        name: 'Not-run',
        data: [],
        color: 'grey',
        metadata: {module: moduleName}

    }];
    moduleInfo["modifyingScriptAllocation"] = false;
    moduleInfo["xValues"] = [];
    moduleInfo["bySoftwareVersion"] = {};
    moduleInfo["showDetailedInfo"] = false;
    moduleInfo["detailedInfo"] = {};
    this.versionList.forEach((softwareVersion) => {
      moduleInfo.bySoftwareVersion[softwareVersion] = {scriptDetailedInfo: {},
        numPassed: 0,
        numFailed: 0,
        numNotRun: 0};

    })
  }

  modifyScriptAllocationClick () {
    this.modifyingScriptAllocation = !this.modifyingScriptAllocation;
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

  parseHistory(moduleInfo, history, scriptPath, softwareVersion) {
    let bySoftwareVersion = moduleInfo.bySoftwareVersion;
    if (bySoftwareVersion.hasOwnProperty(softwareVersion)) {
      let softwareVersionEntry = bySoftwareVersion[softwareVersion];
      let scriptDetailedInfo = softwareVersionEntry.scriptDetailedInfo;
      /*if (!scriptDetailedInfo) {
        softwareVersionEntry.scriptDetailedInfo = {};
        scriptDetailedInfo = softwareVersionEntry.scriptDetailedInfo;
      }*/
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
    }
  }

  fetchScriptInfo(moduleName, moduleInfo) {
    this.apiService.get("/regression/scripts_by_module/" + moduleName).subscribe((response) => {
      let scripts = response.data;
      let numScripts = scripts.length;
      let scriptsFetched = 0;
      scripts.forEach((script) => {
        console.log(script);
        let scriptPath = script.script_path;
        let payload = {};
        payload["script_path"] = scriptPath;
        this.apiService.post("/regression/get_script_history", payload).subscribe((response) => {
          let history = response.data;

          history.forEach((historyElement) => {
            console.log(historyElement);
            let elementSuiteExecutionId = historyElement.suite_execution_id;
            let matchingSoftwareVersion = this.suiteExectionVersionMap[elementSuiteExecutionId];
            this.parseHistory(moduleInfo, historyElement, scriptPath, matchingSoftwareVersion);
          });
          scriptsFetched += 1;
          if (scriptsFetched === numScripts) {
            this.prepareValuesForChart(moduleInfo);
          }


        }, error => {
          scriptsFetched += 1;
          this.loggerService.error("/regression/script_history");
        })
      })
    }, error => {
      this.loggerService.error("Fetching scripts by module");
    })
  }

  fetchRegressionScripts() {
    this.apiService.get("/regression/scripts").subscribe((response) => {
      this.allRegressionScripts = response.data;
      // Set selected modules for each script
      this.allRegressionScripts.forEach((regressionScript) => {
        //console.log("ForEaches");
        regressionScript["selectedModules"] = [];
        regressionScript["savedSelectedModules"] = [];
        regressionScript["dirty"] = false;
        regressionScript.modules.forEach((module) => {
          //console.log("ForEaches2");
          regressionScript.selectedModules.push(this.getMatchingModule(module));
        });
        //regressionScript.selectedModules = [...regressionScript.selectedModules];
        regressionScript.savedSelectedModules = [...regressionScript.selectedModules];
      });
      //console.log(this.allRegressionScripts);
      this.allRegressionScripts = [...this.allRegressionScripts];
      this.fetchUnallocatedRegressionScripts();

    }, error => {
      this.loggerService.error("/regression/scripts");
    })
  }

  fetchUnallocatedRegressionScripts() {
    this.apiService.get("/regression/unallocated_script").subscribe((response) => {
      let unallocatedScripts = response.data;
      unallocatedScripts.forEach((unallocatedScript) => {
        let newEntry = {};
        newEntry["script_path"] = unallocatedScript;
        newEntry["selectedModules"] = [];
        newEntry["savedSelectedModules"] = [];
        newEntry["dirty"] = false;
        this.unallocatedRegressionScripts.push(newEntry);
      });
      console.log(response);
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

}


