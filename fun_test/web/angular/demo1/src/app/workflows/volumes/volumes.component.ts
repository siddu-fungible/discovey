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
  capacity: number = 104857600;
  pool_name: string = null;
  compression_effort = null;
  encryption: boolean = null;
  data_protection: DataProtectionInterface = null;
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
  displayedColumns: string[] = ['name', 'type', 'capacity', 'pool', 'uuid', 'f1', 'encrypt', 'action'];

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

  constructor(private apiService: ApiService, private commonService: CommonService) {
  }

  ngOnInit() {
    this.getVolumes();
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
        this.dataSource.data.push(newVolumeElement);
        this.dataSource.data = [...this.dataSource.data];
      }
      this.refresh();


    }, error => {
      this.refresh();
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
    let volTypeString = "VOL_TYPE_BLK_LOCAL_THIN";
    if (volumeType.toLowerCase() === "durable") {
      volTypeString = "VOL_TYPE_BLK_EC";
    }
    let dp = {vol_type: volTypeString};
    return dp;
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

    let selectedPool = this._getSelectedPool();
    if (!selectedPool) {
      alert("Please select a pool");
      return;
    }

    let volumeType = null;
    if (this.volumeTypeSelection.selected.length === 0) {
      alert("Please select a volume type");
      return;
    }

    volumeType = this.volumeTypeSelection.selected[0];
    let dp = this.getDataProtection(volumeType);
    let payload = {
      capacity: this.addNewVolumeConfig.capacity,
      data_protection: dp,
      name: this.addNewVolumeConfig.name,
      enrypt: this.encryptionOn
    };
    let url = this.commonService.getBaseUrl();
    url = url + "/storage/pools/" + selectedPool + "/volumes";
    this.status = "Creating volume";

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

  attach(volumeUuid) {
    let url = this.commonService.getBaseUrl();
    url = url + "/storage/volumes/" + volumeUuid + "/ports";
    let payload = {"remote_ip": "127.0.0.1"};
    this.apiService.post(url, payload).subscribe((response) => {
      alert("Attached");
      this.getVolumes();
    }, error => {
      alert("Attach failed");
    })
  }

}
