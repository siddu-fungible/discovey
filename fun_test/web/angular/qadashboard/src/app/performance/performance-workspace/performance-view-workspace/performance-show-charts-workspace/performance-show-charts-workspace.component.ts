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
  showPagedItems: boolean = false;

  constructor() {
  }

  ngOnInit() {
  }

  refreshPage(): void {
    this.pagedItems = this.workspace.interested_metrics.slice(this.pager.startIndex, this.pager.endIndex + 1);
    this.showPagedItems = true;
  }

  setPage(pager): void {
    this.pager = pager;
    setTimeout(() => {
      this.refreshPage();
    }, 1);
  }

}
