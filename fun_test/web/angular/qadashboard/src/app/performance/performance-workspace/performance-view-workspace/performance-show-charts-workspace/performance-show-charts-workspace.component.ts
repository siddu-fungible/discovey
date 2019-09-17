import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'performance-show-charts',
  templateUrl: './performance-show-charts-workspace.component.html',
  styleUrls: ['./performance-show-charts-workspace.component.css']
})
export class PerformanceShowChartsWorkspaceComponent implements OnInit {
  @Input() workspace: any = null;
  @Input() buildInfo: any = null;
  pager: any = {};
  pagedItems: any[] = [];

  constructor() { }

  ngOnInit() {
    console.log(this.workspace);
  }

  refreshPage(): void {
    this.pagedItems = this.workspace.interested_metrics.slice(this.pager.startIndex, this.pager.endIndex + 1);
  }

   setPage(pager): void {
    this.pager = pager;
    this.refreshPage()
  }

}
