import {Component, OnInit, ViewChild} from '@angular/core';
import {animate, state, style, transition, trigger} from "@angular/animations";
import {ActionGroup, DpuElement} from "../../dpus/dpus.component";
import {FormControl} from "@angular/forms";
import {SelectionModel} from "@angular/cdk/collections";
import {PoolElement} from "../../pool/pool.component";
import {MatTableDataSource} from "@angular/material";
import {AlertComponent} from "ngx-bootstrap";
import {ApiService} from "../../services/api/api.service";
import {CommonService} from "../../services/common/common.service";
import {VolumeComponent} from "../../volume/volume.component";
import {VolumeElement} from "../../volume/volume.component";
import {PoolsComponent} from "../pools/pools.component";


export interface DataProtectionInterface {
  type: string;
  fault_tolerance: number;
}


export interface AddNewVolumeConfigInterface {
  name: string;
  capacity: number;
  pool_name: string;
  compression_effort: number;
  encryption: boolean;
  data_protection: DataProtectionInterface;
}

export class AddNewVolumeConfig implements AddNewVolumeConfigInterface {
  name: string = null;
  //capacity: number = 104857600;
  capacity: number = 1;
  pool_name: string = null;
  compression_effort = null;
  encryption: boolean = null;
  data_protection: DataProtectionInterface = null;
  type: string = "raw";
}

export interface AddNewVolumeDataProtectionInterface {
  type: string;
  fault_tolerance: number;
}

export class AddNewVolumeDataProtectionConfig implements AddNewVolumeDataProtectionInterface {
  type: string = null;
  fault_tolerance: number = null;
}


const ELEMENT_DATA: VolumeElement[] = [];


@Component({
  selector: 'app-volumes',
  templateUrl: './volumes.component.html',
  styleUrls: ['./volumes.component.css'],
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
      state('stage2', style({opacity: 0, 'width': 0, 'visibility': 'hidden', transform: 'translateX(100%)'})),
      transition('stage1 <=> stage2', animate('225ms')),
    ])]
})
export class VolumesComponent implements OnInit {
  @ViewChild(PoolsComponent) addNewVolumePools: PoolsComponent;


  //displayedColumns: string[] = ['select', 'name', 'type', 'capacity', 'pool', 'uuid', 'f1', 'encrypt', 'action'];
  displayedColumns: string[] = ['delete', 'name', 'type', 'capacity', 'pool', 'uuid', 'f1', 'encrypt', 'action'];

  dataSource = new MatTableDataSource<VolumeElement>(ELEMENT_DATA);
  actionControl = new FormControl();
  selection = new SelectionModel<VolumeElement>(true, []);
  volumeTypeSelection = new SelectionModel<string>(false, []);

  actionSelected: string = null;
  selectedRowIndex: number = null;
  encryptionOn: boolean = true;
  addNewVolumeConfig: AddNewVolumeConfig = new AddNewVolumeConfig();
  addingNewVolume: boolean = false;
  dataProtection: boolean = true;
  showingDetails: boolean = false;
  pools: PoolElement[] = [];
  status: string = null;
  attachingStatus: string = null;
  globalPoolUuid: string = null;
  currentVolumeUnits: string = "GB";
  showingLoadOutput: boolean = false;


  sampleTopology = {
  "f1_id": "0-4",
  "stats": {
    "write_bytes": 0,
    "fault_injection": 0,
    "num_reads": 0,
    "sblk_reads": 0,
    "flvm_block_size": 4096,
    "cache_reads": 0,
    "flvm_vol_size_blocks": 25600,
    "num_writes": 0,
    "sblk_writes": 0,
    "read_bytes": 0,
    "rmw_blks": 0,
    "compact_blks": 0,
    "volume_id": 0,
    "rmw_bytes": 0,
    "type": 6,
    "compact_bytes": 0
  },
  "type": "VOL_TYPE_BLK_LSV",
  "uuid": "9724765456ea43de",
  "src_vols": [
    {
      "f1_id": "0-4",
      "stats": {
        "fault_injection": 0,
        "num_reads": 1,
        "flvm_block_size": 4096,
        "flvm_vol_size_blocks": 38408,
        "volume_id": 0,
        "type": 9,
        "num_writes": 1
      },
      "type": "VOL_TYPE_BLK_EC",
      "uuid": "40c34bb626584022",
      "src_vols": [
        {
          "f1_id": "0-6",
          "stats": {
            "fault_injection": 0,
            "num_reads": 1,
            "flvm_block_size": 4096,
            "flvm_vol_size_blocks": 9603,
            "volume_id": 4096,
            "type": 1,
            "num_writes": 2
          },
          "type": "VOL_TYPE_BLK_LOCAL_THIN",
          "uuid": "c5940a7fe2cb4264",
          "src_vols": []
        },
        {
          "f1_id": "0-7",
          "stats": {
            "fault_injection": 0,
            "num_reads": 0,
            "flvm_block_size": 4096,
            "flvm_vol_size_blocks": 9603,
            "volume_id": 4096,
            "type": 1,
            "num_writes": 2
          },
          "type": "VOL_TYPE_BLK_LOCAL_THIN",
          "uuid": "4f3f049a6af64362",
          "src_vols": []
        },
        {
          "f1_id": "0-1",
          "stats": {
            "fault_injection": 0,
            "num_reads": 0,
            "flvm_block_size": 4096,
            "flvm_vol_size_blocks": 9603,
            "volume_id": 4096,
            "type": 1,
            "num_writes": 2
          },
          "type": "VOL_TYPE_BLK_LOCAL_THIN",
          "uuid": "f0ff6f3854554900",
          "src_vols": []
        },
        {
          "f1_id": "0-2",
          "stats": {
            "fault_injection": 0,
            "num_reads": 0,
            "flvm_block_size": 4096,
            "flvm_vol_size_blocks": 9603,
            "volume_id": 4096,
            "type": 1,
            "num_writes": 2
          },
          "type": "VOL_TYPE_BLK_LOCAL_THIN",
          "uuid": "e995a7d2d25a4f94",
          "src_vols": []
        },
        {
          "f1_id": "0-3",
          "stats": {
            "fault_injection": 0,
            "num_reads": 0,
            "flvm_block_size": 4096,
            "flvm_vol_size_blocks": 9603,
            "volume_id": 4096,
            "type": 1,
            "num_writes": 2
          },
          "type": "VOL_TYPE_BLK_LOCAL_THIN",
          "uuid": "cb5a3aebd8f94d4f",
          "src_vols": []
        },
        {
          "f1_id": "0-8",
          "stats": {
            "fault_injection": 0,
            "num_reads": 0,
            "flvm_block_size": 4096,
            "flvm_vol_size_blocks": 9603,
            "volume_id": 4096,
            "type": 1,
            "num_writes": 2
          },
          "type": "VOL_TYPE_BLK_LOCAL_THIN",
          "uuid": "2896e640f9c34b89",
          "src_vols": []
        }
      ]
    },
    {
      "f1_id": "0-4",
      "stats": {
        "fault_injection": 0,
        "num_reads": 0,
        "flvm_block_size": 512,
        "flvm_vol_size_blocks": 2048,
        "volume_id": 16384,
        "type": 5,
        "num_writes": 0
      },
      "type": "VOL_TYPE_BLK_NV_MEMORY",
      "uuid": "551a3c50ca834e64",
      "src_vols": []
    }
  ]
};


  constructor(private apiService: ApiService, private commonService: CommonService) {
  }

  ngOnInit() {
    this.getGlobalPool();
    this.getVolumes();
    let i = 0;
  }

  refresh() {
    if (this.dataSource.data.length === 0) {
      this.getVolumes();
    }
    setTimeout(() => this.refresh(), 1000);
  }

  getVolumes() {
    let url = this.commonService.getBaseUrl();
    if (!url) {
      setTimeout(() => {
        this.getVolumes();
      }, 1000);
      return;
    }

    url = url + "/storage/volumes";
    this.status = "Fetching volumes";
    this.apiService.get(url).subscribe((response) => {
      this.status = null;
      this.dataSource.data = [];
      let volumesData = response.data;
      for (let key in volumesData) {
        let value = volumesData[key];
        let newVolumeElement: VolumeElement = new VolumeElement();
        newVolumeElement.f1 = value.f1;
        newVolumeElement.uuid = value.uuid;
        newVolumeElement.encrypt = value.encrypt;
        newVolumeElement.capacity = value.capacity;
        newVolumeElement.type = value.type;
        newVolumeElement.pool = value.pool;
        newVolumeElement.name = value.name;
        if (value.hasOwnProperty('port')) {
          newVolumeElement.port = value.port;
        } else {
          newVolumeElement.port = null;
        }


        this.dataSource.data.push(newVolumeElement);
        this.dataSource.data = [...this.dataSource.data];
      }

    }, error => {
      //this.refresh();
    });
  }

  getSchemeValue(scheme): string {
    let result = "ec";
    if (scheme === "Replication") {
      result = "replication"
    }
    return result;
  }

  getVolumeTypeSchemeValue(scheme): string {
    let result = "durable";
    if (scheme === "Raw") {
      result = "raw";
    }
    return result;
  }

  step = 0;

  setStep(index: number) {
    this.step = index;
  }

  nextStep() {
    this.step++;
  }

  prevStep() {
    this.step--;

  }

  /** Whether the number of selected elements matches the total number of rows. */
  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }


  /** Selects all rows if they are not all selected; otherwise clear selection. */
  masterToggle() {
    this.isAllSelected() ?
      this.selection.clear() :
      this.dataSource.data.forEach(row => this.selection.select(row));
  }

  stageAnimationDone($event) {
    if ($event.toState === "stage2") {
    }
    console.log("Animation done");
  }

  private _getSelectedPool() {
    let pe = this.addNewVolumePools.getSelected();
    let poolName = null;
    pe.forEach((pe) => {
      //console.log(pe.name);
      poolName = pe.uuid;
    });
    return poolName;
  }

  getDataProtection(volumeType) {
    let dp;
    let volTypeString = "VOL_TYPE_BLK_LOCAL_THIN";
    if (volumeType.toLowerCase() === "durable") {
      volTypeString = "VOL_TYPE_BLK_EC";
       dp = {vol_type: volTypeString, num_failed_disks: 2};
    } else {

      dp = {vol_type: volTypeString};
    }

    return dp;
  }

  getGlobalPool() {
    let result = null;
        let url = this.commonService.getBaseUrl();
    if (!url) {
      setTimeout(() => {
        this.getGlobalPool();
      }, 50);
      return;
    }
    url = url + "/storage/pools";
    this.apiService.get(url).subscribe((response) => {
      let pools = response.data;
      let poolIds = Object.keys(pools);
      poolIds.forEach((poolId) => {
        let newPoolElement: PoolElement = new PoolElement();
        newPoolElement.uuid = poolId;
        newPoolElement.f1s = pools[poolId].f1s;
        this.pools.push(newPoolElement);
        this.globalPoolUuid = newPoolElement.uuid;
      })
    }, error => {

    });

    return result;
  }

  submit() {
    if (!this.addNewVolumeConfig.name) {
      alert("Please specify a name");
      return;
    }

    if (!this.addNewVolumeConfig.capacity) {
      alert("Please specify a capacity");
      return;
    }
    let capacity = this.addNewVolumeConfig.capacity * 1024 * 1024 * 1024;
    let selectedPool = this.globalPoolUuid; //this._getSelectedPool();

    if (!selectedPool) {
      alert("Please select a pool");
      return;
    }

    /*
    let volumeType = null;
    if (this.volumeTypeSelection.selected.length === 0) {
      alert("Please select a volume type");
      return;
    }*/

    if (!this.addNewVolumeConfig.type) {
      alert("Please select a volume type");
      return;
    }

    //volumeType = this.volumeTypeSelection.selected[0];
    //let dp = this.getDataProtection(volumeType);
    let dp = this.getDataProtection(this.addNewVolumeConfig.type);

    let payload = {
      capacity: capacity,
      data_protection: dp,
      name: this.addNewVolumeConfig.name,
      encrypt: this.encryptionOn
    };

    if (this.addNewVolumeConfig.type === 'durable') {
      payload["compress"] = 4;
    }


    let url = this.commonService.getBaseUrl();
    url = url + "/storage/pools/" + selectedPool + "/volumes";
    this.status = "Creating volume";

    //let payload = {"capacity": 104857600, "data_protection": {"vol_type": "VOL_TYPE_BLK_EC", "num_failed_disks": 2}, "name": "repvol2", "compress": 4, "encrypt": true};


    this.apiService.post(url, payload).subscribe((response) => {
      alert("Volume added");
      this.getVolumes();
      this.addingNewVolume = false;
      this.status = null;
    }, error => {
      this.status = null;

    });


    /*
    let url = this.commonService.getBaseUrl();
    url = url + "/storage/pools";
    this.apiService.get(url).subscribe( (response) => {
      let pools = response.data;
      let poolIds = Object.keys(pools);

      let url = this.commonService.getBaseUrl();
      url = url + "/storage/pools/" + poolIds[0] + "/volumes";
      let payload = {"capacity": 104857600, "data_protection": {"vol_type": "VOL_TYPE_BLK_LOCAL_THIN"}, "name": "repvol1"};
      let payload = {"capacity": 104857600, "data_protection": {"vol_type": "VOL_TYPE_BLK_EC", "num_failed_disks": 2, "encrypt": true}, "name": "repvol2", "compress": 4};
      let payload = {"capacity": 104857600, "data_protection": {"vol_type": "VOL_TYPE_BLK_EC", "num_failed_disks": 2}, "name": "repvol2", "compress": 4};

      this.apiService.post(url, payload).subscribe((response)=> {
        alert("Volume added");
        this.getVolumes();
        this.addingNewVolume = false;
      }, error => {

      });
    }, error => {
    });*/


  }

  whatSelection() {
    console.log(this.volumeTypeSelection);
    console.log("hi");
  }

  attach(element, volumeUuid) {
    let url = this.commonService.getBaseUrl();
    url = url + "/storage/volumes/" + volumeUuid + "/ports";
    let payload = {}; //{"remote_ip": "127.0.0.1"};
    element.attachingStatus = "Attaching...";
    this.apiService.post(url, payload).subscribe((response) => {
      alert("Attached");
      element.attachingStatus = "Refreshing";
      this.getVolumes();
    }, error => {
      alert("Attach failed");
      element.attachingStatus = null;
    })
  }

  test() {
    console.log(this.addNewVolumeConfig.type);
    console.log(this.currentVolumeUnits);
  }

  deleteVolume(volumeUuid) {
    let url = this.commonService.getBaseUrl();
    url = url + "/storage/volumes/" + volumeUuid;
    this.status = "Deleting volume";
    this.apiService.delete(url).subscribe((response) => {
      this.status = null;
      alert("Volume deleted");
      this.getVolumes();

    }, error => {
      alert("Delete failed");
    })
  }

}
