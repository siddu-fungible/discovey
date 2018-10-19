import {Component} from '@angular/core';
import {animate, state, style, transition, trigger} from '@angular/animations';

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
export class VolumeComponent {
  dataSource = ELEMENT_DATA;
  columnsToDisplay = ['name',
    'type',
    'capacity',
    'compression_effort',
    'encrypted',
    'namespace_id',
    'pool_name',
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
    "encrypted": "Encrypted",
    "namespace_id": "Namespace ID",
    "pool_name": "Pool",
    "read_iops": "Read IOPS",
    "write_iops": "Write IOPS"
  };
  expandedElement: VolumeElement;

  constructor() {
    this.columnsToDisplay = Object.keys(this.columnToHeader);
  }

}

export interface VolumeElement {
  name: string;
  type: string;
  capacity: number;
  description: string;
  compression_effort: number;
  encrypted: boolean;
  namespace_id: number;
  num_data_volumes: number;
  num_parity_volumes: number;
  num_replica_volumes: number;
  pool_name: string;
  read_iops: number;
  write_iops: number;
  dpus: string[];

}

const ELEMENT_DATA: VolumeElement[] = [
  {
    name: "Volume-1",
    type: 'EC',
    capacity: 1024,
    compression_effort: 1,
    encrypted: true,
    namespace_id: 233,
    num_data_volumes: 4,
    num_parity_volumes: 2,
    num_replica_volumes: 3,
    pool_name: "Pool-1",
    description: `Some description`,
    read_iops: 14,
    write_iops: 54,
    dpus: ["DPU-1", "DPU-2"]
  }

];


/**  Copyright 2018 Google Inc. All Rights Reserved.
 Use of this source code is governed by an MIT-style license that
 can be found in the LICENSE file at http://angular.io/license */

