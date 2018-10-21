import {Component, Input, OnInit} from '@angular/core';
import {ActionGroup, DpuElement} from "../dpus/dpus.component";
import {FormControl} from "@angular/forms";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {SelectionModel} from "@angular/cdk/collections";
import {MatTableDataSource} from "@angular/material";

export interface ControllerElement {
  id: number;
  ip: string;
  port: number;
}

const ELEMENT_DATA: ControllerElement[] = [
  {id: 0, ip: 'qa-ubuntu-02', port: 50022}
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
  selector: 'app-storage-controller',
  templateUrl: './storage-controller.component.html',
  styleUrls: ['./storage-controller.component.css'],

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
export class StorageControllerComponent implements OnInit {
  @Input() action: boolean = true;
  @Input() radioSelection: boolean = true;

  //displayedColumns: string[] = ['select', 'name', 'capacity', 'volumes', 'dpus'];
  displayedColumns: string[] = []; //['name', 'capacity', 'volumes', 'dpus'];

  dataSource = new MatTableDataSource<ControllerElement>(ELEMENT_DATA);
  actionControl = new FormControl();
  actionSelected: string = null;
  selectedRowIndex: number = null;
  selectedElement: string = null;
  selection = new SelectionModel<ControllerElement>(true, []);
  displayedVolumesColumns: string[] = ['position', 'name', 'weight', 'symbol'];
  expandedElement: ControllerElement;
  volumes = VOLUME_DATA;
  addingNewController: boolean = true;

  constructor() {


  }

    actionGroups: ActionGroup[] = [
    {name: "Storage", actions: [{value: 1, viewValue: "Add a new pool"}]}
  ];


  ngOnInit() {

        if (this.radioSelection) {
      this.displayedColumns = ['active', 'health', 'ip', 'port'];
    } else {
      this.displayedColumns = ['active', 'health', 'name', 'capacity', 'volumes', 'dpus'];
    }
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
    const pe: ControllerElement = {id: 0, ip: "qa-ubuntu-02", port: 50022};
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

  public getSelected(): ControllerElement[] {
    return this.selection.selected;
  }

}
