import { Component, OnInit } from '@angular/core';
import {ActionGroup, DpuElement} from "../../dpus/dpus.component";
import {FormControl} from "@angular/forms";

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


@Component({
  selector: 'app-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.css']
})
export class PoolsComponent implements OnInit {
  displayedColumns: string[] = ['name', 'capacity', 'volumes'];
  dataSource = ELEMENT_DATA;
  actionControl = new FormControl();
  actionSelected: string = null;
  selectedRowIndex: number = null;
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
    setTimeout(()=>{    //<<<---    using ()=> syntax
      this.selectedRowIndex = null;
    }, 2000);

  }

}
