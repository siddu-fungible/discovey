import { Component, OnInit } from '@angular/core';
import {CommonService, Controller, TopoF1} from "../services/common/common.service";
import {ApiService} from "../services/api/api.service";

@Component({
  selector: 'app-topology',
  templateUrl: './topology.component.html',
  styleUrls: ['./topology.component.css']
})
export class TopologyComponent implements OnInit {
  activeController: Controller = null;
  topoF1s: TopoF1[] = [];

  constructor(private commonService: CommonService, private apiService: ApiService) {

  }

  ngOnInit() {
    //console.log("topo init");
    this.activeController = this.commonService.getActiveController();
    this.fetchTopology();
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
        this.topoF1s.push(newF1);
      }
    }, error => {

    })


  }

}
