import {Component, OnInit, Input, Output, EventEmitter} from '@angular/core';
import {Sort} from '@angular/material';
import {PagerService} from '../services/pager.service';

@Component({
  selector: 'fun-table',
  templateUrl: './fun-table.component.html',
  styleUrls: ['./fun-table.component.css']
})

export class FunTableComponent implements OnInit {
  range: number;
  headers: any[];
  rows: any[];

  constructor( private pagerService: PagerService) {
  }

  // private allItems: any = [];
  pager: any = {};
  pagedItems: any[];
  originalData: any[];
  @Input() data: any = [];
  @Output() nextPage: EventEmitter <number> = new EventEmitter();

  ngOnInit() {
    // console.log("Data check:" +this.data);
    this.rows = this.data["rows"];
    this.headers = this.data["headers"];
    // console.log("Allitems:" +this.allItems);
    // console.log("Allitems rows:" +this.allItems["rows"]);
    this.originalData = Array.from(this.rows);

    this.setPage(1);
  }

  setPage(page: number) {
    // get pager object from service
    if(!this.data["all"]) {
      this.nextPage.emit(page);
    }
    else {
      this.pager = this.pagerService.getPager(this.data["length"], page, 10);
      this.pagedItems = this.rows.slice(this.pager.startIndex, this.pager.endIndex + 1);
    }

  }

  paging(page: number) {
    this.pager = this.pagerService.getPager(this.data["length"], page, this.rows.length);
    this.pagedItems = this.rows.slice(0, this.rows.length);
  }

  ngOnChanges() {
    this.rows = this.data["rows"];
    this.headers = this.data["headers"];
    this.originalData = Array.from(this.rows);
    this.paging(this.data["currentPageIndex"]);
    //this.setPage(1);
  }

  sortData(sort: Sort) {
    if (!sort.active || sort.direction === '') {
      this.pagedItems = Array.from(this.originalData);
      this.rows = this.pagedItems;
      this.setPage(1);
      return;
    }

    this.pagedItems = this.rows.sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      if (sort.active) {
        return compare(a[sort.active], b[sort.active], isAsc);
      }
    });
    this.setPage(1);
  }

}

function compare(a, b, isAsc) {
  return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
}
