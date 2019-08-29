import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'performance-show-charts',
  templateUrl: './performance-show-charts-workspace.component.html',
  styleUrls: ['./performance-show-charts-workspace.component.css']
})
export class PerformanceShowChartsWorkspaceComponent implements OnInit {
  @Input() workspace: any = null;
  @Input() buildInfo: any = null;

  constructor() { }

  ngOnInit() {
  }

}
