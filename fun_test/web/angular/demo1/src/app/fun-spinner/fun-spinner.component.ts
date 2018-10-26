import {Component, OnInit, Input, OnChanges} from '@angular/core';

@Component({
  selector: 'fun-spinner',
  template: "<div [hidden]='status === null'>" +
            "<span><i class='fa fa-refresh fa-spin fa-2x fa-fw' style='color: green'></i>Status: {{ status }}</span>" +
            "</div>",
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
