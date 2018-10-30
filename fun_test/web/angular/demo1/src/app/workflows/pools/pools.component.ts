import {Component, Input, OnInit} from '@angular/core';
import {ActionGroup, DpuElement} from "../../dpus/dpus.component";
import {FormControl} from "@angular/forms";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {SelectionModel} from "@angular/cdk/collections";
import {MatTableDataSource} from "@angular/material";
import {CommonService} from "../../services/common/common.service";
import {ApiService} from "../../services/api/api.service";
import {PoolElement} from "../../pool/pool.component";



const ELEMENT_DATA: PoolElement[] = [
  /*
  {id: 0, name: 'Pool-1', capacity: 1024, volumes: [1, 2, 3], dpus:[1, 2, 3]},
  {id: 1, name: 'Pool-2', capacity: 2048, volumes: [2, 3], dpus: [2, 3]}*/
];


export interface VolumeElement {
  name: string;
  position: number;
  weight: number;
  symbol: string;
}

const VOLUME_DATA: VolumeElement[] = [
  {position: 1, name: 'Hydrogen', weight: 1.0079, symbol: 'H'},
  {position: 2, name: 'Helium', weight: 4.0026, symbol: 'He'}
];


@Component({
  selector: 'app-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.css'],
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
export class PoolsComponent implements OnInit {
  @Input() action: boolean = true;
  @Input() radioSelection: boolean = false;

  //displayedColumns: string[] = ['select', 'name', 'capacity', 'volumes', 'dpus'];
  displayedColumns: string[] = []; //['name', 'capacity', 'volumes', 'dpus'];

  dataSource = new MatTableDataSource<PoolElement>(ELEMENT_DATA);
  actionControl = new FormControl();
  actionSelected: string = null;
  selectedRowIndex: number = null;
  selectedElement: string = null;
  selection = new SelectionModel<PoolElement>(true, []);
  displayedVolumesColumns: string[] = ['position', 'name', 'weight', 'symbol'];
  expandedElement: PoolElement;
  volumes = VOLUME_DATA;
  pools: PoolElement[] = [];

  constructor(private commonService: CommonService, private apiService: ApiService) {


  }

    actionGroups: ActionGroup[] = [
    {name: "Storage", actions: [{value: 1, viewValue: "Add a new pool"}]}
  ];


  ngOnInit() {
    console.log("Pools oninit");

        if (this.radioSelection) {
      this.displayedColumns = ['select', 'pool_name', 'uuid', 'f1s'];
    } else {
      this.displayedColumns = ['select', 'pool_name', 'uuid', 'f1s'];
    }
    this.getPools();

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

    getPools() {
    this.pools = [];
    let url = this.commonService.getBaseUrl();
    if (!url) {
      setTimeout(() => {
        this.getPools();
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
      })
    }, error => {

    });
    this.dataSource = new MatTableDataSource<PoolElement>(this.pools);

  }

  submit() {
    const pe: PoolElement = {uuid: "123", f1s: ["1-2"]};
    this.dataSource.data.push(pe);
    this.dataSource.data = [...this.dataSource.data];
    this.actionSelected = null;
    this.selectedRowIndex = this.dataSource.data.length - 1;
    setTimeout(()=> {
      this.selectedRowIndex = null;
    }, 2000);

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

  public getSelected(): PoolElement[] {
    return this.selection.selected;
  }

  toggleExpandedElement(row) {
    if (this.expandedElement) {
      this.expandedElement = null;
    } else {
      this.expandedElement = row;
    }
  }

}
