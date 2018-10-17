import {Component, OnInit, Input, OnChanges} from '@angular/core';

@Component({
  selector: 'fun-spinner',
  templateUrl: './fun-spinner.component.html',
  styleUrls: ['./fun-spinner.component.css']
})
export class FunSpinnerComponent implements OnInit, OnChanges {
@Input() hideOnIdle: boolean;
@Input() status: string;

  constructor() { }

  ngOnInit() {
    console.log(this.hideOnIdle);
  }

  ngOnChanges() {
    console.log(this.hideOnIdle);
  }

}
