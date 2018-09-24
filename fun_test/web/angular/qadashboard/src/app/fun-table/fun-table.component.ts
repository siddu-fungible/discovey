import {Component, OnInit, Input, Output, EventEmitter} from '@angular/core';
import {Sort} from '@angular/material';
import {PagerService} from '../services/pager/pager.service';
import {LoggerService} from "../services/logger/logger.service";
import {logger} from "../../../node_modules/codelyzer/util/logger";

@Component({
  selector: 'fun-table',
  templateUrl: './fun-table.component.html',
  styleUrls: ['./fun-table.component.css']
})

export class FunTableComponent implements OnInit {
  headers: any[];
  rows: any[];
  pageSize: number;
  hideShowColumns: boolean = false;
  static readonly defaultPageSize: number = 10;

  constructor(private pagerService: PagerService, private logger: LoggerService) {
    this.logger.log("FunTableComponent init");
  }

  // private allItems: any = [];
  pager: any = {};
  pagedItems: any[];
  // originalData: any[];
  @Input() data: any = [];
  @Output() nextPage: EventEmitter<number> = new EventEmitter();

  ngOnInit() {
    if (this.data.rows && this.data.rows.length === 10000) {
      this.logger.log("10000 rows");
    }
  }

  //setting the page number
  setPage(page: number) {
    // get pager object from service
    if (!this.data.all) {
      this.nextPage.emit(page);
    }
    else {
      this.setPagedItems(page);
    }
  }

  //setting the rows to be displayed by the template
  setPagedItems(page: number) {
    this.pager = this.pagerService.getPager(this.data.totalLength, page, this.pageSize);
    if (this.data.all) {
      this.pagedItems = this.rows.slice(this.pager.startIndex, this.pager.endIndex + 1);
    }
    else {
      this.pagedItems = this.rows.slice(0, this.pageSize);
    }
  }

  ngOnChanges() {
    if (this.data.currentPageIndex < 0) {
      this.logger.fatal("Page Index is less than 1");
    }
    else {
      this.rows = this.data.rows;
      this.headers = this.data.headers;
      // this.originalData = Array.from(this.rows);
      if (this.data.pageSize) {
        this.pageSize = this.data.pageSize;
      }
      else {
        this.pageSize = FunTableComponent.defaultPageSize;
      }
      this.setPagedItems(this.data.currentPageIndex);
      //this.setPage(1);
    }
  }

  //sorts the input rows in the data
  sortData(sort: Sort) {
    if (!sort.active || sort.direction === '') {
      // this.pagedItems = Array.from(this.originalData);
      // this.rows = this.pagedItems;
      // this.setPage(1);
      return;
    }
    this.pagedItems = this.rows.sort((a, b) => {
      const isAscending = sort.direction === 'asc';
      if (sort.active) {
        return compare(a[sort.active], b[sort.active], isAscending);
      }
    });
    this.setPage(1);
  }

  //toggle between hide and show columns
  editColumns() {
    this.logger.log("Open form is entered");
    this.hideShowColumns = !this.hideShowColumns;
  }

  submit() {
    this.logger.log("submitted the column change");
    this.hideShowColumns = false;
    //change the headers.
  }

}

function compare(a, b, isAsc) {
  return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
}
