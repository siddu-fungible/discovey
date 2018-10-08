import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-demo1',
  templateUrl: './demo1.component.html',
  styleUrls: ['./demo1.component.css']
})
export class Demo1Component implements OnInit {

  sideBarClass: boolean = true;
  constructor() { }

  ngOnInit() {
  }

  sideBarCollapseClick() {
    this.sideBarClass = !this.sideBarClass;
  }

}
