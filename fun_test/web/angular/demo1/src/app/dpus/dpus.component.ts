import {SelectionModel} from '@angular/cdk/collections';
import {Component} from '@angular/core';
import {MatTableDataSource} from '@angular/material';
import {animate, state, style, transition, trigger} from '@angular/animations';
import {FormControl} from '@angular/forms';


export interface DpuElement {
  name: string;
  position: number;
  online: boolean;
  num_raw_volumes: number;
}

const ELEMENT_DATA: DpuElement[] = [
  {position: 1, name: 'DPU-1', online: true, num_raw_volumes: 4},
  {position: 2, name: 'DPU-2', online: true, num_raw_volumes: 5},
  {position: 3, name: 'DPU-3', online: true, num_raw_volumes: 7},
];


export interface Action {
  value: number;
  viewValue: string;
}

export interface ActionGroup {
  name: string;
  actions: Action[];
}

export interface WorkFlowStage {

}

export interface WorkFlow {
  name: string;
  currentStageIndex: number;
  stages: WorkFlowStage[];
}


/**
 * @title Table with selection
 */
@Component({
  selector: 'dpus',
  styleUrls: ['dpus.component.css'],
  templateUrl: 'dpus.component.html',
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
export class DpusComponent {
  displayedColumns: string[] = ['select', 'position', 'name', 'online', 'num_raw_volumes'];
  dataSource = new MatTableDataSource<DpuElement>(ELEMENT_DATA);
  selection = new SelectionModel<DpuElement>(true, []);
  expandedElement: DpuElement;
  actionControl = new FormControl();
  actionSelected: string = null;
  started: boolean = false;
  currentStage: string = "stage1";


  actionGroups: ActionGroup[] = [
    {name: "Storage", actions: [{value: 1, viewValue: "Create Raw Volume"}]}
  ];

  constructor() {

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
      this.started = true;
    }
    console.log("Animation done");
  }
}


/**  Copyright 2018 Google Inc. All Rights Reserved.
 Use of this source code is governed by an MIT-style license that
 can be found in the LICENSE file at http://angular.io/license */
