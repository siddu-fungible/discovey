import {Component, OnInit} from '@angular/core';
import {animate, state, style, transition, trigger} from '@angular/animations';
import {ActivatedRoute} from "@angular/router";
import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";
import {CommonService, TopoF1} from "../services/common/common.service";
import {MatTableDataSource} from "@angular/material";


/**
 * @title Table with expandable rows
 */
@Component({
  selector: 'app-volume',
  styleUrls: ['./volume.component.css'],
  templateUrl: './volume.component.html',
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({height: '0px', minHeight: '0', display: 'none'})),
      state('expanded', style({height: '*'})),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})
export class VolumeComponent implements OnInit {
  status: string = null;
  uuid: string = null;
  name: string = null;
  showingLoadPanel: boolean = false;
  //dataSource = ELEMENT_DATA;
  dataSource = new MatTableDataSource<VolumeElement>();
  volumeElement: VolumeElement;
  bgPollCount: number = 0;
  loadOutput: string = null;
  volumeTypes = {ec: "EC", lsv: "LSV"};
  columnsToDisplay = ['name',
    'type',
    'capacity',
    'compression_effort',
    'encrypt',
    'namespace_id',
    'pool',
    'num_data_volumes',
    'num_parity_volumes',
    'num_replica_volumes',
    'read_iops',
    'write_iops',
    'dpus',
  'actions',
  'more_info'];

  columnToHeader = {
    'name': "Name",
    "type": "Type",
    "capacity": "Capacity",
    "compression_effort": "Compression effort",
    "encrypt": "Encrypted",
    "namespace_id": "Namespace ID",
    "pool": "Pool",
    "read_iops": "Read IOPS",
    "write_iops": "Write IOPS",
    'actions': "Actions",
    'more_info': ""
  };
  expandedElement: VolumeElement;

  constructor(private apiService: ApiService, private commonService: CommonService, private route: ActivatedRoute) {
    this.columnsToDisplay = ["name", "type", "capacity", "encrypt", "pool", "read_iops", "actions", "more_info"];
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['name']) {
        this.uuid = params['name'];
      }
    });
    this.getVolumeInfo();
  }

  fetchTg(tgName) {

  }


  getVolumeInfo() {
    if (this.uuid) {
      let url = this.commonService.getBaseUrl();
      if (!url) {
        setTimeout(() => {
        this.getVolumeInfo();
        }, 1000);
        return;
      }
      this.dataSource.data = [];
      url = url + "/storage/volumes/" + this.uuid;
      this.status = "Fetching volume info";
      this.apiService.get(url).subscribe((response) => {
        let value = response.data;
        this.volumeElement = new VolumeElement();
        this.volumeElement.f1 = value.f1;
        this.volumeElement.uuid = value.uuid;
        this.volumeElement.encrypt = value.encrypt;
        this.volumeElement.capacity = value.capacity;
        this.volumeElement.type = value.type;
        this.volumeElement.pool = value.pool;
        this.volumeElement.name = value.name;
        if (value.hasOwnProperty('port')) {
          this.volumeElement.port = value.port;
          console.log(this.commonService.tgMap[this.volumeElement.port.tg]);
        } else {
          this.volumeElement.port = null;
        }
        this.dataSource.data.push(this.volumeElement);
        this.dataSource.data = [...this.dataSource.data];
        this.status = null;

      }, error => {
        this.status = null;
      })


    }
  }

  attach(element, volumeUuid) {
    let url = this.commonService.getBaseUrl();
    url = url + "/storage/volumes/" + volumeUuid + "/ports";
    let payload = {}; //{"remote_ip": "127.0.0.1"};
    element.attachingStatus = "Attaching...";
    this.apiService.post(url, payload).subscribe((response) => {
      alert("Attached");
      element.attachingStatus = "Refreshing";
      this.getVolumeInfo();
    }, error => {
      alert("Attach failed");
      element.attachingStatus = null;
    })
  }

  pollStatus(executionId) {
    this.bgPollCount++;
    let url = "/demo/bg_job_status";
    let payload = {bg_execution_id: executionId};
    this.apiService.post(url, payload).subscribe((response) => {
      console.log(response.data.status + ":" + response.data.output);
      let executionStatus = response.data.status;
      if (executionStatus !== "PASSED" && executionStatus !== "FAILED") {
        setTimeout(() => {
          this.pollStatus(executionId);
          }, 5000);
      } else {
        this.loadOutput = response.data.output;
      }



    }, error => {

    });


  }


  testBg() {
    let url = "/demo/schedule_fio_job";
    let payload = {};
    this.apiService.post(url, payload).subscribe((response) => {
      let bgExecutionId = response.data;
      let payload = {bg_execution_id: bgExecutionId};
      this.bgPollCount = 0;
      this.pollStatus(bgExecutionId);
      console.log("BgExecutionID:" + bgExecutionId);
    }, error => {

    });
  }


  _doSendTraffic(context) {
    let url = "/demo/schedule_fio_job";
    let payload = {traffic_context: context};
    this.apiService.post(url, payload).subscribe((response) => {
      let bgExecutionId = response.data;
      let payload = {bg_execution_id: bgExecutionId};
      this.pollStatus(bgExecutionId);
      console.log("BgExecutionID:" + bgExecutionId);
    }, error => {

    });
  }

  sendTraffic() {
    let result = null;
    let url = this.commonService.getBaseUrl();
    url = url + '/topology/get_spec';
    this.apiService.get(url).subscribe((response) => {
      console.log(response);
      let data = response.data;
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
          if (newF1.tgs) {
            for (let key2 of Object.keys(newF1.tgs)) {
              if (key2 === this.volumeElement.port.tg) {
                result = newF1.tgs[key2];
                let payload = {};
                payload["f1_ip"] = this.volumeElement.port.ip;
                payload["tg_ip"] = this.volumeElement.port.remote_ip;
                payload["tg_mgmt_ip"] = result.mgmt_ip;
                payload["tg_mgmt_port"] = result.mgmt_ssh_port;
                console.log(payload);
                this._doSendTraffic(payload);
              }
            }
          }

        }
      }
    }, error => {

    })

  }

}

export class VolumeElement {
  name: string;
  uuid: string;
  f1: string;
  type: string;
  capacity: number;
  description: string;
  compression_effort: number;
  encrypt: boolean;
  namespace_id: number;
  num_data_volumes: number;
  num_parity_volumes: number;
  num_replica_volumes: number;
  pool: string;
  read_iops: number;
  write_iops: number;
  dpus: string[];
  attached: boolean = false;
  port: any = {};
  attachingStatus: string = null;

}

const ELEMENT_DATA: VolumeElement[] = [
];




/**  Copyright 2018 Google Inc. All Rights Reserved.
 Use of this source code is governed by an MIT-style license that
 can be found in the LICENSE file at http://angular.io/license */

