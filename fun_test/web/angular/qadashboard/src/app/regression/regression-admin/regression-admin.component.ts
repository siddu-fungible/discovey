import { Component, OnInit } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";

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
  constructor(private apiService: ApiService, private loggerService: LoggerService) { }
  xValues: any [] = [];
  y1Values = [];
  tempPassedValues = [];
  tempFailedValues = [];
  tempNotRunValues = [];
  tempSoftwareVersions = [];


  ngOnInit() {
    this.fetchAllVersions();
    this.y1Values = [{
        name: 'Passed',
        data: []
    }, {
        name: 'Failed',
        data: []
    }, {
        name: 'Not-run',
        data: []
    }]
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

  fetchModules () {
    this.apiService.get("/regression/modules").subscribe((response) => {
      console.log(response);
      let modules = response.data;
      modules.forEach((module) => {
        this.info[module.name] = {name: module.name, verboseName: module.verbose_name};
        this.prepareVersionPlaceHolders(this.info[module.name]);
        this.fetchScriptInfo(module.name, this.info[module.name]);
      })
    }, error => {
      this.loggerService.error("Error fetching modules");
    })
  }

  prepareVersionPlaceHolders (moduleInfo) {
    // create a bySoftwareVersion key under each module
    // byVersion is an array of software versions
    moduleInfo["num"]
    moduleInfo["bySoftwareVersion"] = {};
    this.versionList.forEach((softwareVersion) => {
      moduleInfo.bySoftwareVersion[softwareVersion] = {scriptDetailedInfo: {},
        numPassed: 0,
        numFailed: 0,
        numNotRun: 0};

    })
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
      if (!scriptDetailedInfo.hasOwnProperty(scriptPath)) {
        scriptDetailedInfo[scriptPath] = [];
      }
      scriptDetailedInfo[scriptPath].push(history);
      let historyResults = this.aggregateHistoryResults(history);
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
    console.log(this.xValues);
    Object.keys(moduleInfo.bySoftwareVersion).forEach((softwareVersion) => {
      let intSoftwareVersion = parseInt(softwareVersion);
      let numPassed = moduleInfo.bySoftwareVersion[intSoftwareVersion].numPassed;
      let numFailed = moduleInfo.bySoftwareVersion[intSoftwareVersion].numFailed;
      let numNotRun = moduleInfo.bySoftwareVersion[intSoftwareVersion].numNotRun;
      let total = numPassed + numFailed + numNotRun;
      if (total) {
        this.xValues.push(intSoftwareVersion);
        this.y1Values[0].data.push(numPassed);
        this.y1Values[1].data.push(numFailed);
        this.y1Values[2].data.push(numNotRun);
        this.xValues = [...this.xValues];
        this.y1Values = [...this.y1Values];
      }


    })
        console.log(this.xValues);

  }

  test() {
    console.log(this.info);
  }

}


