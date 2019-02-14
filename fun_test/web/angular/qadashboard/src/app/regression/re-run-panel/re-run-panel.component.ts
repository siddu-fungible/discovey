import {Component, Input, OnChanges, OnInit} from '@angular/core';

@Component({
  selector: 'app-re-run-panel',
  templateUrl: './re-run-panel.component.html',
  styleUrls: ['./re-run-panel.component.css']
})
export class ReRunPanelComponent implements OnInit, OnChanges {
  @Input() reRunInfo = null;

  constructor() { }

  ngOnInit() {
    let i = 0;
  }

  ngOnChanges() {
  }

}
