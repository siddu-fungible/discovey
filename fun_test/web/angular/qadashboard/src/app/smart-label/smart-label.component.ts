import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-smart-label',
  templateUrl: './smart-label.component.html',
  styleUrls: ['./smart-label.component.css']
})
export class SmartLabelComponent implements OnInit {
  @Input() type: string = null;
  @Input() value: string;
  @Input() simulateLink: boolean = false;
  constructor() { }

  ngOnInit() {
    this.type = this.type.toLowerCase();
  }

}
