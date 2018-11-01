import { Component, OnInit } from '@angular/core';
import {CommonService, Controller, TopoF1, TopoTg} from "../services/common/common.service";
import {ApiService} from "../services/api/api.service";
import {MatTableDataSource} from "@angular/material";
import {ControllerElement} from "../storage-controller/storage-controller.component";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {SelectionModel} from "@angular/cdk/collections";
import {PoolElement} from "../pool/pool.component";

class Load {
  attribute: string;
  value: string;
}

@Component({
  selector: 'app-topology',
  templateUrl: './topology.component.html',
  styleUrls: ['./topology.component.css'],
      animations: [
    trigger('detailExpand', [
      state('collapsed', style({height: '0px', minHeight: '0', display: 'none'})),
      state('expanded', style({height: '*'})),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
    trigger('enterAnimation', [
      transition(':enter', [
        style({transform: 'translateX(100%)', opacity: 0}),
        animate('500ms')
      ]),
      transition(':leave', [
        style({transform: 'translateX(0)', opacity: 1}),
        animate('500ms')
      ])
    ]),
  trigger('nextStage', [
      state('stage1', style({opacity: 1, 'width': '100%'})),
      state('stage2', style({ opacity: 0, 'width': 0, 'visibility': 'hidden', transform: 'translateX(100%)'})),
      transition('stage1 <=> stage2', animate('225ms')),
    ])]
})
export class TopologyComponent implements OnInit {
  activeController: Controller = null;
  topoF1s: TopoF1[] = [];
  dataSource = new MatTableDataSource<TopoF1>();
  //displayedColumns: string[] = ['name', 'dataplane_ip', 'mgmt_ip', 'mgmt_ssh_port', 'action'];
  displayedColumns: string[] = ['name', 'dataplane_ip', 'cpu', 'action'];

  displayedTgColumns: string[] = ['name', 'dataplane_ip', 'mgmt_ip', 'mgmt_ssh_port', 'action'];
  displayedLoadColumns: string[] = ['attribute', 'value'];
  expandedElement: TopoF1;
  selection = new SelectionModel<TopoF1>(false, []);
  loadF1: TopoF1 = null;
  loadTg: TopoTg = null;
  showingLoadWindow: boolean = false;
  loadDataSource: MatTableDataSource<Load> = null;
  bgPollCount: number = 0;
  loadOutput: string = null;
  maxBgPoll: number = 20;
  loadStopped: boolean = true;
  showingAgentLog: boolean = false;
  currentAgengLogF1: TopoF1 = null;
  tgMap: {[name: string]: TopoTg} = this.commonService.getTgMap();


  constructor(private commonService: CommonService, private apiService: ApiService) {

  }

  ngOnInit() {
    //console.log("topo init");
    this.activeController = this.commonService.getActiveController();
    this.fetchTopology();
  }

  attachTg(f1) {
    let url = this.commonService.getBaseUrl();
    url = url + "/topology/attach_tg";
    let payload = {f1: f1.name};
    console.log(payload);
    this.apiService.post(url, payload).subscribe((response) => {
      this.fetchTopology();

    }, error => {

    });
  }

  getTgDataSource(tgs) {
    // typescript iterate dictionary
    let tgList = [];
    for (let key in tgs) {
      let value = tgs[key];
      value.name = key;
      tgList.push(value);
    }
    return new MatTableDataSource<TopoTg>(tgList);

  }

  fetchDpuStat(f1) {
    let url = this.commonService.getBaseUrl();
    url = url + "/storage/f1/" + f1.name;
    this.apiService.get(url, false).subscribe((response) => {
      f1.cpu = response.data.cpu;
    }, error => {

    });

    setTimeout(() => {this.fetchDpuStat(f1)}, 3000);
  }




  fetchTopology() {
    let url = this.commonService.getBaseUrl();
    if (!url) {
      setTimeout(() => {
        this.fetchTopology();
      }, 1000);
      return;
    }
    this.activeController = this.commonService.getActiveController();


    url = url + '/topology/get_spec';
    this.apiService.get(url).subscribe((response) => {
      console.log(response);
      let data = response.data;
      this.topoF1s = [];
      let f1s = data.F1;
      for (let key of Object.keys(f1s)) {
        let newF1 = new TopoF1();
        newF1.name = key;
        newF1.mgmt_ip = f1s[key].mgmt_ip;
        newF1.mgmt_ssh_port = f1s[key].mgmt_ssh_port;
        newF1.dataplane_ip = f1s[key].dataplane_ip;
        newF1.storage_agent_port = f1s[key].storage_agent_port;
        this.fetchDpuStat(newF1);
        if (f1s[key].hasOwnProperty("tgs")) {
          newF1.tgs = f1s[key].tgs;
          if (newF1.tgs) {
            for (let key2 of Object.keys(newF1.tgs)) {
              this.tgMap[key2] = newF1.tgs[key2];
            }
          }

        }
        this.topoF1s.push(newF1);
        this.dataSource.data = this.topoF1s;
      }
    }, error => {

    })
  }

  tgsExist(tgs) {
    let tgNames = Object.keys(tgs);
    return tgNames.length;
  }

  load(f1, tg) {
    this.loadF1 = f1;
    this.loadTg = tg;
    console.log(this.loadF1);
    console.log(this.loadTg);
    this.loadDataSource = new MatTableDataSource<Load>([{attribute: "DPU", value: this.loadF1.name},
      {attribute: "TG", value: this.loadTg.name}]);
    this.showingLoadWindow = true;
    this.scroll();
  }

  scroll() {
    let x = document.querySelector("#load-div");
    if (x){
        x.scrollIntoView();
    }
  }

  sendTraffic() {
    let url = "/demo/schedule_fio_job";
    let payload = {};
    this.apiService.post(url, payload).subscribe((response) => {
      this.bgPollCount = 0;
      this.loadStopped = false;
      let bgExecutionId = response.data;
      let payload = {bg_execution_id: bgExecutionId};
      this.pollStatus(bgExecutionId);
      console.log("BgExecutionID:" + bgExecutionId);
    }, error => {

    });
  }

  pollStatus(executionId) {
    this.bgPollCount++;
    let url = "/demo/bg_job_status";
    let payload = {bg_execution_id: executionId};
    this.apiService.post(url, payload).subscribe((response) => {
      console.log(response.data.status + ":" + response.data.output);
      let executionStatus = response.data.status;
      if (executionStatus !== "PASSED" && executionStatus !== "FAILED" && (this.bgPollCount < this.maxBgPoll)) {
        setTimeout(() => {
          this.pollStatus(executionId);
        }, 5000);
      } else {
        this.loadOutput = response.data.output;
        this.loadStopped = true;
      }

      if (this.bgPollCount >= this.maxBgPoll) {
        this.loadStopped = true;
      }


    }, error => {

    });
  }

  showAgentLog(f1Name, f1MgmtIp, f1MgmtSshPport) {
    this.showingAgentLog = !this.showingAgentLog;
  }

  fetchAgentLog(topoF1) {
    this.currentAgengLogF1 = topoF1;
    console.log(topoF1);
  }

  getTgInfo() {

  }


}
