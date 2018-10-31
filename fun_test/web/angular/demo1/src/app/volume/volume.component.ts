import {Component, OnInit} from '@angular/core';
import {animate, state, style, transition, trigger} from '@angular/animations';
import {ActivatedRoute} from "@angular/router";
import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";
import {CommonService, TopoF1} from "../services/common/common.service";
import {MatTableDataSource} from "@angular/material";


export class TopologyVolumeElement {
  f1_id: string = null;
  type: string = null;
  indent: number = 0;
  uuid: string = null;
  stats: any = {};
}

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
  loadMaxWaitTime: number = 60;
  bgPollCount: number = this.loadMaxWaitTime;
  loadOutput: string = null;
  loadReadIops: number = 0;
  loadWriteIops: number = 0;
  volumeTypes = {ec: "EC", lsv: "LSV"};
  topoVolElements: TopologyVolumeElement[] = [];
  topologyFetchStatus: string = null;

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
    'num_reads',
    'num_writes',
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
    "num_reads": "Reads",
    "num_writes": "Writes",
    'actions': "Actions",
    'more_info': ""
  };
  expandedElement: VolumeElement;

  constructor(private apiService: ApiService, private commonService: CommonService, private route: ActivatedRoute) {
    this.columnsToDisplay = ["name", "type", "capacity", "encrypt", "pool", "num_reads", "num_writes", "actions", "more_info"];
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['name']) {
        this.uuid = params['name'];
      }
    });
    this.getVolumeInfo();
  }

  resetLoadCounters() {
    this.bgPollCount = 0;
    this.loadReadIops = 0;
    this.loadWriteIops = 0;
    this.loadOutput = null;
  }


  fetchTg(tgName) {

  }


  getVolumeTopology(uuid) {
    let url = this.commonService.getBaseUrl();
    if (!url) {
      setTimeout(() => {
      this.getVolumeTopology(uuid);
      }, 1000);
      return;
    }
    url = url + "/storage/volumes/" + uuid + "/topology";

    this.topologyFetchStatus = "Fetching underlying volume(s) info";
    this.apiService.get(url).subscribe((response)=> {
      this.topologyFetchStatus = null;
      this.topoVolElements = [];
      this.descendTopoTree(response.data);
    }, error => {

    })
  }

  getVolumeInfo(disableStatus = false) {
    if (this.uuid) {
      let url = this.commonService.getBaseUrl();
      if (!url) {
        setTimeout(() => {
        this.getVolumeInfo(disableStatus);
        }, 1000);
        return;
      }

      url = url + "/storage/volumes/" + this.uuid;
      this.status = "Fetching volume info";
      if (disableStatus) {
        this.status = null;
      }
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

        if (value.hasOwnProperty('stats')) {
          this.volumeElement.stats = value.stats;
        }

        this.dataSource.data = [];
        this.dataSource.data.push(this.volumeElement);
        this.dataSource.data = [...this.dataSource.data];
        this.status = null;
        this.getVolumeTopology(this.volumeElement.uuid);

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
    this.apiService.post(url, payload, false).subscribe((response) => {
      console.log(response.data.status + ":" + response.data.output);
      let executionStatus = response.data.status;
      if (executionStatus !== "PASSED" && executionStatus !== "FAILED" && (this.bgPollCount < this.loadMaxWaitTime)) {
        setTimeout(() => {
          this.pollStatus(executionId);
          }, 1000);
        //this.getVolumeInfo(true);
      } else {
        this.loadOutput = response.data.output;
        this.loadOutput = this.loadOutput.replace("\n", "<br>");
        //this.loadOutput = 'fun_nvmeof: (g=0): rw=rw, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=fun, iodepth=8 fio-3.3 Starting 1 process fun_nvmeof: Laying out IO file (1 file / 0MiB) Client IP=172.16.0.33, F1 IP=172.16.0.38, number of NS=1, IO Queues = 1, Mode = IO_ONLY and NQN = nqn.2017-05.com.fungible:nss-uuid1 Connected on RD socket 1099 Initiating ADMIN connection...Received Admin Connect Response Sending Fabric Property Set Command ...Received Property Set Response Initiating I/O connection 1...Received IO Connect Response fun_nvmeof: (groupid=0, jobs=1): err= 0: pid=199: Sun Oct 28 04:41:06 2018 read: IOPS=83, BW=333KiB/s (341kB/s)(60.0KiB/180msec) slat (nsec): min=29416, max=87638, avg=51622.00, stdev=15989.47 clat (usec): min=11975, max=60745, avg=29234.12, stdev=12966.38 lat (usec): min=12021, max=60776, avg=29285.75, stdev=12962.79 clat percentiles (usec): | 1.00th=[11994], 5.00th=[11994], 10.00th=[13173], 20.00th=[16057], | 30.00th=[23725], 40.00th=[23725], 50.00th=[28705], 60.00th=[31589], | 70.00th=[34341], 80.00th=[35390], 90.00th=[42730], 95.00th=[60556], | 99.00th=[60556], 99.50th=[60556], 99.90th=[60556], 99.95th=[60556], | 99.99th=[60556] write: IOPS=94, BW=378KiB/s (387kB/s)(68.0KiB/180msec) slat (nsec): min=22242, max=76884, avg=50544.82, stdev=17253.61 clat (usec): min=28957, max=84685, avg=51442.52, stdev=15233.17 lat (usec): min=29020, max=84725, avg=51493.07, stdev=15232.74 clat percentiles (usec): | 1.00th=[28967], 5.00th=[28967], 10.00th=[38536], 20.00th=[38536], | 30.00th=[43254], 40.00th=[44303], 50.00th=[46400], 60.00th=[55837], | 70.00th=[55837], 80.00th=[61080], 90.00th=[83362], 95.00th=[84411], | 99.00th=[84411], 99.50th=[84411], 99.90th=[84411], 99.95th=[84411], | 99.99th=[84411] lat (msec) : 20=12.50%, 50=62.50%, 100=25.00% cpu : usr=4.47%, sys=0.00%, ctx=994, majf=0, minf=40 IO depths : 1=3.1%, 2=9.4%, 4=40.6%, 8=46.9%, 16=0.0%, 32=0.0%, >=64=0.0% submit : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0% complete : 0=0.0%, 4=95.8%, 8=4.2%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0% issued rwt: total=15,17,0, short=0,0,0, dropped=0,0,0 latency : target=0, window=0, percentile=100.00%, depth=8 Run status group 0 (all jobs): READ: bw=333KiB/s (341kB/s), 333KiB/s-333KiB/s (341kB/s-341kB/s), io=60.0KiB (61.4kB), run=180-180msec WRITE: bw=378KiB/s (387kB/s), 378KiB/s-378KiB/s (387kB/s-387kB/s), io=68.0KiB (69.6kB), run=180-180msec \n';
        let reg = /read: IOPS=(\d+)/g;
        let match = reg.exec(this.loadOutput);
        if (match) {
          this.loadReadIops = parseInt(match[1]);
        }
        reg = /write: IOPS=(\d+)/g;
        match = reg.exec(this.loadOutput);
        if (match) {
          this.loadWriteIops = parseInt(match[1]);
        }

        this.bgPollCount = this.loadMaxWaitTime;
        this.getVolumeInfo(true);
      }
    }, error => {

    });

  }

  descendTopoTree(node, indent = 0) {
    let topoVolElement = new TopologyVolumeElement();
    topoVolElement.f1_id = node.f1_id;
    topoVolElement.type = node.type;
    topoVolElement.indent = indent;
    topoVolElement.uuid = node.uuid;
    topoVolElement.stats = node.stats;
    this.topoVolElements.push(topoVolElement);

    node.src_vols.forEach((src_vol) => {
      this.descendTopoTree(src_vol, indent + 1);
    });
  }

  getIndentHtml = (node) => {
    let s = "";
    if (node.hasOwnProperty("indent")) {
      for (let i = 0; i < 2 * (node.indent - 1); i++) {
        s += "<span style=\"color: white\">&rarr;</span>";
      }
      if (node.indent)
        s += "<span>&nbsp;&nbsp;</span>";
    }

    return s;
  };

  refresh() {
    this.getVolumeInfo();
  }

  getLoadProgress() {
    return (this.bgPollCount * 100/this.loadMaxWaitTime);
  }


  _doSendTraffic(context) {
    let url = "/demo/schedule_fio_job";
    let payload = {traffic_context: context};
    this.bgPollCount = 0;
    this.resetLoadCounters();
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
                payload["tg_mgmt_ssh_port"] = result.mgmt_ssh_port;
                payload["ns_id"] = this.volumeElement.port.nsid;
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
  stats: any = {};

}

const ELEMENT_DATA: VolumeElement[] = [
];




/**  Copyright 2018 Google Inc. All Rights Reserved.
 Use of this source code is governed by an MIT-style license that
 can be found in the LICENSE file at http://angular.io/license */

