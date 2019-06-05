import {Component, Input, OnChanges, OnInit} from '@angular/core';

@Component({
  selector: 'app-smart-label',
  templateUrl: './smart-label.component.html',
  styleUrls: ['./smart-label.component.css']
})
export class SmartLabelComponent implements OnInit, OnChanges {
  @Input() type: string = null;
  @Input() value: string;
  @Input() simulateLink: boolean = false;
  constructor() { }

  ngOnInit() {
    /*if (this.type) {
      this.type = this.type.toLowerCase();
    }*/
  }

  ngOnChanges() {
    if (this.type) {
      this.type = this.type.toLowerCase();
    } else {
      if (this.value) {
        if (this.value === "IN_PROGRESS") {
          this.type = "info";
        } else if (this.value === "COMPLETED" || this.value.toLowerCase() === "passed") {
          this.type = "passed";
        } else if (this.value.toLowerCase() === "failed" || this.value.toLowerCase() === "error") {
          this.type = "failed";
        } else {
          this.type = "info";
        }
      }

    }
  }

}
