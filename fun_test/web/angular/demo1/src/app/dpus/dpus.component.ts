import {SelectionModel} from '@angular/cdk/collections';
import {Component} from '@angular/core';
import {MatTableDataSource} from '@angular/material';
import {animate, state, style, transition, trigger} from '@angular/animations';
import {FormControl} from '@angular/forms';



export interface PeriodicElement {
  name: string;
  position: number;
  online: boolean;
  num_raw_volumes: number;
}

const ELEMENT_DATA: PeriodicElement[] = [
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
    ])]
})
export class DpusComponent {
  displayedColumns: string[] = ['select', 'position', 'name', 'online', 'num_raw_volumes'];
  dataSource = new MatTableDataSource<PeriodicElement>(ELEMENT_DATA);
  selection = new SelectionModel<PeriodicElement>(true, []);
  expandedElement: PeriodicElement;
  actionControl = new FormControl();


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
}


/**  Copyright 2018 Google Inc. All Rights Reserved.
    Use of this source code is governed by an MIT-style license that
    can be found in the LICENSE file at http://angular.io/license */
