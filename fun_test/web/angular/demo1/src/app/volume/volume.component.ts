import {Component, OnInit} from '@angular/core';
import {animate, state, style, transition, trigger} from '@angular/animations';
import {ActivatedRoute} from "@angular/router";
import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";
import {CommonService} from "../services/common/common.service";
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
  //dataSource = ELEMENT_DATA;
  dataSource = new MatTableDataSource<VolumeElement>();

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
    'dpus'];

  columnToHeader = {
    'name': "Name",
    "type": "Type",
    "capacity": "Capacity",
    "compression_effort": "Compression effort",
    "encrypt": "Encrypted",
    "namespace_id": "Namespace ID",
    "pool": "Pool",
    "read_iops": "Read IOPS",
    "write_iops": "Write IOPS"
  };
  expandedElement: VolumeElement;

  constructor(private apiService: ApiService, private commonService: CommonService, private route: ActivatedRoute) {
    this.columnsToDisplay = ["name", "type", "capacity", "encrypt", "pool", "read_iops"];
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['name']) {
        this.uuid = params['name'];
      }
    });
    this.getVolumeInfo();
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
      url = url + "/storage/volumes/" + this.uuid;
      this.status = "Fetching volume info";
      this.apiService.get(url).subscribe((response) => {
        let value = response.data;
        let newVolumeElement: VolumeElement = new VolumeElement();
        newVolumeElement.f1 = value.f1;
        newVolumeElement.uuid = value.uuid;
        newVolumeElement.encrypt = value.encrypt;
        newVolumeElement.capacity = value.capacity;
        newVolumeElement.type = value.type;
        newVolumeElement.pool = value.pool;
        newVolumeElement.name = value.name;
        this.dataSource.data.push(newVolumeElement);
        this.dataSource.data = [...this.dataSource.data];
        this.status = null;

      }, error => {
        this.status = null;
      })


    }
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

}

const ELEMENT_DATA: VolumeElement[] = [
  {
    f1: "1",
    uuid: "1",
    name: "Volume-1",
    type: 'EC',
    capacity: 1024,
    compression_effort: 1,
    encrypt: true,
    namespace_id: 233,
    num_data_volumes: 4,
    num_parity_volumes: 2,
    num_replica_volumes: 3,
    pool: "Pool-1",
    description: `Some description`,
    read_iops: 14,
    write_iops: 54,
    dpus: ["DPU-1", "DPU-2"],
    attached: false
  }

];


/**  Copyright 2018 Google Inc. All Rights Reserved.
 Use of this source code is governed by an MIT-style license that
 can be found in the LICENSE file at http://angular.io/license */

