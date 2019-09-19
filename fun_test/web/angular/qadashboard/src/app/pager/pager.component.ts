import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {PagerService} from "../services/pager/pager.service";

@Component({
  selector: 'app-pager',
  templateUrl: './pager.component.html',
  styleUrls: ['./pager.component.css']
})
export class PagerComponent implements OnInit {
  pager: any = {};
  @Input() data: any = [];
  @Output() pageNumber: EventEmitter<any> = new EventEmitter();
  currentPage: number = 1;
  @Input() recordsPerPage: number = 10;

  constructor(private pagerService: PagerService) { }

  ngOnInit() {
    this.refreshPager();
  }

  refreshPager(): void {
     this.pager = this.pagerService.getPager(this.data.length, this.currentPage, this.recordsPerPage);
     this.pageNumber.emit(this.pager);
  }

  setPage(pageNumber): void {
    this.currentPage = pageNumber;
    this.refreshPager();
  }

}
