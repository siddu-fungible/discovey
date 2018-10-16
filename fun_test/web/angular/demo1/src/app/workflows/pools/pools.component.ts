import { Component, OnInit } from '@angular/core';
import {ActionGroup, DpuElement} from "../../dpus/dpus.component";
import {FormControl} from "@angular/forms";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {SelectionModel} from "@angular/cdk/collections";

export interface PoolElement {
  id: number;
  name: string;
  capacity: number;
  volumes: number[];
}

const ELEMENT_DATA: PoolElement[] = [
  {id: 0, name: 'Pool-1', capacity: 1024, volumes: [1, 2, 3]},
  {id: 1, name: 'Pool-2', capacity: 2048, volumes: [2, 3]}
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
  displayedColumns: string[] = ['name', 'capacity', 'volumes'];
  dataSource = ELEMENT_DATA;
  actionControl = new FormControl();
  actionSelected: string = null;
  selectedRowIndex: number = null;
    selection = new SelectionModel<PoolElement>(true, []);
  displayedVolumesColumns: string[] = ['position', 'name', 'weight', 'symbol'];

    expandedElement: PoolElement;
  volumes = VOLUME_DATA;

  constructor() { }

    actionGroups: ActionGroup[] = [
    {name: "Storage", actions: [{value: 1, viewValue: "Add a new pool"}]}
  ];


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

  submit() {
    const pe: PoolElement = {name: 'Pool-3', capacity: 1024, volumes: [1, 2, 3], id: this.dataSource.length};
    this.dataSource.push(pe);
    this.dataSource = [...this.dataSource];
    this.actionSelected = null;
    this.selectedRowIndex = this.dataSource.length - 1;
    setTimeout(()=> {
      this.selectedRowIndex = null;
    }, 2000);

  }

}
