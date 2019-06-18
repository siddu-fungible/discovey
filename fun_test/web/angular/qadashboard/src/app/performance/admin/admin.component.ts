import {Component, OnInit, ViewChild} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {Title} from "@angular/platform-browser";
import {CommonService} from "../../services/common/common.service";
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})

export class AdminComponent implements OnInit {
  status: string = null;
  metricsList: any[] = [];
  modules: any;
  modelsInfo: any;
  selectedModule: any = null;
  previewDataSets: any;
  ADMIN_URL: string = "/performance/admin";

  constructor(
    private apiService: ApiService,
    private loggerService: LoggerService,
    private title: Title,
    private commonService: CommonService,
    private activatedRoute: ActivatedRoute,
    private router: Router
  ) {
  }

  ngOnInit() {
    console.log("Component Init");
    this.title.setTitle('Admin');
    this.status = "Loading";
    this.metricsList = [];
    this.fetchModules();
    this.modelsInfo = {};
    this.status = null;
  }

  fetchModules(): void {
    this.apiService.get("/regression/modules").subscribe(response => {
            this.modules = response.data;
            this.modules.forEach((module) => {
                let moduleName = module.name;
            })
        }, error => {
      this.loggerService.error("fetchModules");
    })
  }

  addChartClick(modelName): void {
    let url = this.ADMIN_URL + "/create/" + modelName;
    window.open(url, '_blank');
  }

  editChartClick(metricId, modelName): void {
    let url = this.ADMIN_URL + "/edit/" + modelName + "/" + metricId;
    window.open(url, '_blank');
    
  }
  
  showScores(metricId): void {
    let url = this.ADMIN_URL + "/scores/" + metricId;
    window.open(url, '_blank');
  }

  showData(metricId): void {
    let url = this.ADMIN_URL + "/data/" + metricId;
    window.open(url, '_blank');
  }

  moduleChange(): void {
    let payload = {};
    let thisModule = this.selectedModule;
        if (this.selectedModule) {
            payload["module_name"] = this.selectedModule;
            this.apiService.post("/metrics/models_by_module", payload).subscribe((models) => {
                this.modelsInfo[thisModule] = models.data;
            }, error => {
              this.loggerService.error("moduleChange")
            })
        }
  }

}
