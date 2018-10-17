import {Component, OnInit, Input, OnChanges} from '@angular/core';

@Component({
  selector: 'fun-spinner',
  templateUrl: './fun-spinner.component.html',
  styleUrls: ['./fun-spinner.component.css']
})
export class FunSpinnerComponent implements OnInit, OnChanges {
@Input() status: string;

  constructor() { }

  ngOnInit() {
    console.log(this.status);
  }

  ngOnChanges() {
    console.log(this.status);
  }

}
