import {Component, Input, OnInit} from '@angular/core';
import {PagerService} from "../../../../services/pager/pager.service";

@Component({
  selector: 'performance-show-charts',
  templateUrl: './performance-show-charts-workspace.component.html',
  styleUrls: ['./performance-show-charts-workspace.component.css']
})
export class PerformanceShowChartsWorkspaceComponent implements OnInit {
  @Input() workspace: any = null;
  @Input() buildInfo: any = null;
  pager: any = {};
  currentPage: number = 1;
  RECORDS_PER_PAGE: number = 4;
  pagedItems: any[] = [];

  constructor(private pagerService: PagerService) { }

  ngOnInit() {
    this.refreshPage();
  }

  refreshPage(): void {
    this.pager = this.pagerService.getPager(this.workspace.interested_metrics.length, this.currentPage, this.RECORDS_PER_PAGE);
    this.pagedItems = this.workspace.interested_metrics.slice(this.pager.startIndex, this.pager.endIndex + 1);
  }

   setPage(pageNumber): void {
    this.currentPage = pageNumber;
    this.refreshPage()
  }

}
