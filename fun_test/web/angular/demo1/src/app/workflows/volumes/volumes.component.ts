import { Component, OnInit } from '@angular/core';
import {animate, state, style, transition, trigger} from "@angular/animations";
import {ActionGroup, DpuElement} from "../../dpus/dpus.component";
import {FormControl} from "@angular/forms";
import {SelectionModel} from "@angular/cdk/collections";
import {PoolElement} from "../pools/pools.component";
import {MatTableDataSource} from "@angular/material";


export interface VolumeElement {
  id: number;
  name: string;
  capacity: number;
  pool: string;
}

const ELEMENT_DATA: VolumeElement[] = [
  {id: 0, name: 'Volume-1', capacity: 1024, pool: "Pool-1"},
  {id: 1, name: 'Volume-2', capacity: 2048, pool: "Pool-2"}
];



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
      state('stage2', style({ opacity: 0, 'width': 0, 'visibility': 'hidden', transform: 'translateX(100%)'})),
      transition('stage1 <=> stage2', animate('225ms')),
    ])]
})
export class VolumesComponent implements OnInit {
  displayedColumns: string[] = ['select', 'name', 'capacity', 'pool'];
  dataSource = new MatTableDataSource<VolumeElement>(ELEMENT_DATA);
    actionControl = new FormControl();
    selection = new SelectionModel<VolumeElement>(true, []);
  actionSelected: string = null;
  selectedRowIndex: number = null;


    dataProtection: boolean = true;
   actionGroups: ActionGroup[] = [
    {name: "Storage", actions: [{value: 1, viewValue: "Add a new volume"}]}
  ];

  constructor() { }

  ngOnInit() {
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

    submit() {
    const pe: VolumeElement =  {id: 1, name: 'Volume-3', capacity: 2048, pool: "Pool-3"};

    this.dataSource.data.push(pe);
    this.dataSource.data = [...this.dataSource.data];
    this.actionSelected = null;
    this.selectedRowIndex = this.dataSource.data.length - 1;
    setTimeout(()=> {
      this.selectedRowIndex = null;
    }, 2000);

  }


}
