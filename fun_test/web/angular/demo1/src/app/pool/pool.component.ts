import { Component, OnInit } from '@angular/core';

export class PoolElement {
  uuid: string;
  f1s: string[];
}

@Component({
  selector: 'app-pool',
  templateUrl: './pool.component.html',
  styleUrls: ['./pool.component.css']
})
export class PoolComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}
