import {Component, OnInit, Input} from '@angular/core';
import {ApiService} from "../../../services/api/api.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {CommonService} from "../../../services/common/common.service";

@Component({
  selector: 'charts-list',
  templateUrl: './charts-list.component.html',
  styleUrls: ['./charts-list.component.css']
})
export class ChartsListComponent implements OnInit {

  @Input() metricId: any = null;
  modelName: string = null;
  modelNames: string[] = [];
  owners: string[] = [];
  owner: string = null;
  chartName: string = null;
  chartNames: string[] = [];
  showCharts: boolean = false;

  constructor(private apiService: ApiService, private loggerService: LoggerService, private route: ActivatedRoute,
              private commonService: CommonService) {
  }

  ngOnInit() {
    if (this.metricId) {
      this.fetchModelNames();
      this.fetchOwners();
    }
  }

  fetchModelNames(): void {
    this.apiService.get("/metrics/fetch_models").subscribe(response => {
      this.modelNames = response.data;
    }, error => {
      this.loggerService.error("fetch_models")
    });
  }

  fetchOwners(): void {
    this.apiService.get("/metrics/fetch_owners").subscribe(response => {
      this.owners = response.data;
    }, error => {
      this.loggerService.error("fetch_owners")
    });
  }

  moduleChange(): void {
    let payload = {};
    payload["model_name"] = this.modelName;
    payload["owner"] = this.owner;
    if (this.modelName && this.owner) {
      this.apiService.post("/metrics/fetch_charts", payload).subscribe(response => {
        this.chartNames = response.data;
        this.chartName = null;
        this.showCharts = true;
      }, error => {
        this.loggerService.error("fetch_charts")
      });
    }
  }
}
