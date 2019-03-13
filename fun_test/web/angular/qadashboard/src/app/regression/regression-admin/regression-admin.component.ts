import {Component, OnInit} from '@angular/core';
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
  adminOption: string = "Categorize scripts";
  filterData = null; //{info: "Networking overall", payload: {module: "networking"}}];
  scriptPathsList = []; // sorted list of script paths;

  constructor(private apiService: ApiService, private loggerService: LoggerService, private commonService: CommonService) {
  }

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

  byScriptName: any = {};
  scriptPathSelected: string = null;

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
    //this.filterData.push({info: "Networking overall", payload: {module: "networking"}});
  }

  refreshSummary() {
    this.filterData = [];
    this.filterData.push({info: this.scriptPathSelected, payload: {script_path: this.scriptPathSelected}});
  }

  fetchAllVersions() {
    this.apiService.get("/regression/get_all_versions").subscribe((response) => {
      let entries = response.data;
      entries.forEach((entry) => {
        let version = parseInt(entry.version);
        this.versionSet.add(version);
        this.suiteExectionVersionMap[entry.execution_id] = version;

      });
      //console.log(this.versionSet);
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


  fetchModules() {
    this.apiService.get("/regression/modules").subscribe((response) => {
      // console.log(response);
      this.availableModules = response.data;
      this.availableModules.forEach((module) => {
        this.info[module.name] = {name: module.name, verboseName: module.verbose_name};
        this.fetchRegressionScripts();
      });
    }, error => {
      this.loggerService.error("Error fetching modules");
    })
  }

  modifyScriptAllocationClick() {
    this.modifyingScriptAllocation = !this.modifyingScriptAllocation;
    this.fetchRegressionScripts();
  }


  populateByScriptName() {
    let scriptPaths = new Set();
    this.allRegressionScripts.forEach(scriptEntry => {
      scriptPaths.add(scriptEntry.script_path);
    });
    this.scriptPathsList = Array.from(scriptPaths);
    this.scriptPathsList.sort();
    if (this.scriptPathsList.length) {
      this.scriptPathSelected = this.scriptPathsList[0];
    }

  }


  fetchRegressionScripts() {
    this.apiService.get("/regression/scripts").subscribe((response) => {
      this.allRegressionScripts = response.data;
      this.populateByScriptName();
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
      this.unallocatedRegressionScripts = [];
      unallocatedScripts.forEach((unallocatedScript) => {
        let newEntry = {};
        newEntry["script_path"] = unallocatedScript;
        newEntry["selectedModules"] = [];
        newEntry["savedSelectedModules"] = [];
        newEntry["dirty"] = false;
        this.unallocatedRegressionScripts.push(newEntry);
      });
      // console.log(response);
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
    //console.log(regressionScript.selectedModules);
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


  test() {
    console.log(this.info);
    console.log(this.info["storage"].detailedInfo.scriptDetailedInfo);
  }

  /*
  public functionCalledOnEachIteration(index, item) {
    debugger;
    console.log('trackByFn', index, item);
    return item;
  }*/

}


