import { Component, OnInit } from '@angular/core';
import {CommonService, Controller, TopoF1, TopoTg} from "../services/common/common.service";
import {ApiService} from "../services/api/api.service";
import {MatTableDataSource} from "@angular/material";
import {ControllerElement} from "../storage-controller/storage-controller.component";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {SelectionModel} from "@angular/cdk/collections";
import {PoolElement} from "../workflows/pools/pools.component";

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
  displayedColumns: string[] = ['name', 'dataplane_ip', 'mgmt_ip', 'mgmt_ssh_port', 'action'];
  displayedTgColumns: string[] = ['name', 'dataplane_ip', 'mgmt_ip', 'mgmt_ssh_port'];
  expandedElement: TopoF1;
  selection = new SelectionModel<TopoF1>(false, []);


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

  fetchTopology() {
    let url = this.commonService.getBaseUrl();
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
        if (f1s[key].hasOwnProperty("tgs")) {
          newF1.tgs = f1s[key].tgs;
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

}
