import {Component, Input, OnChanges, OnInit} from '@angular/core';
import {RegressionService} from "../regression.service";

@Component({
  selector: 'app-re-run-panel',
  templateUrl: './re-run-panel.component.html',
  styleUrls: ['./re-run-panel.component.css']
})
export class ReRunPanelComponent implements OnInit, OnChanges {
  @Input() reRunInfo = null;

  constructor(private regressionService: RegressionService) { }

  ngOnInit() {
    let i = 0;
  }

  ngOnChanges() {
  }

  localizeTime(t) {
    return this.regressionService.getPrettyLocalizeTime(t);
  }
}
