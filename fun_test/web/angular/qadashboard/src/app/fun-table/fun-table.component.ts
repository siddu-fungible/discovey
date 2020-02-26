import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output
} from '@angular/core';
import {Sort} from '@angular/material';
import {PagerService} from '../services/pager/pager.service';
import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";
import {CommonService} from "../services/common/common.service";

@Component({
  selector: 'fun-table',
  templateUrl: './fun-table.component.html',
  styleUrls: ['./fun-table.component.css'],
  changeDetection: ChangeDetectionStrategy.Default
})

export class FunTableComponent implements OnInit {
  headers: any[];
  rows: any[];
  pageSize: number;
  hideShowColumns: boolean = false;
  headerIndexMap: Map<number, boolean> = new Map<number, boolean>();
  static readonly defaultPageSize: number = 10;
  TIMEZONE: string = "America/Los_Angeles";

  constructor(private apiService: ApiService, private pagerService: PagerService, private logger: LoggerService, private commonService: CommonService) {
    console.log("FunTableComponent init");
  }

  pager: any = {};
  pagedItems: any[];
  @Input() data: any = [];
  @Output() nextPage: EventEmitter<number> = new EventEmitter();

  ngOnInit() {
  }

  //setting the page number
  setPage(page: number): void {
    // get pager object from service
    if (!this.data.all) {
      this.nextPage.emit(page);
    } else {
      this.setPagedItems(page);
    }
  }

  //setting the rows to be displayed by the template
  setPagedItems(page: number): void {
    this.pager = this.pagerService.getPager(this.data.totalLength, page, this.pageSize);
    if (this.data.all) {
      this.pagedItems = this.rows.slice(this.pager.startIndex, this.pager.endIndex + 1);
    } else {
      this.pagedItems = this.rows.slice(0, this.pageSize);
    }
  }

  ngOnChanges() {
    if (this.data.currentPageIndex < 0) {
      this.logger.error("Page Index is less than 1");
    } else {
      this.rows = this.data.rows;
      this.headers = this.data.headers;
      for (let i in this.headers) {
        this.headerIndexMap.set(Number(i), true);
      }
      if (this.data.pageSize) {
        this.pageSize = this.data.pageSize;
      } else {
        this.pageSize = FunTableComponent.defaultPageSize;
      }
      this.setPagedItems(this.data.currentPageIndex);
    }
  }

  //sorts the input rows in the data
  sortData(sort: Sort): any {
    if (!sort.active || sort.direction === '') {
      return;
    }
    this.pagedItems = this.rows.sort((a, b) => {
      const isAscending = sort.direction === 'asc';
      if (sort.active) {
        return this.compare(a[sort.active], b[sort.active], isAscending);
      }
    });
    this.setPage(1);
  }

  //compares the objects from sortData
  compare(a, b, isAsc): any {
    return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
  }

  //toggle between hide and show columns
  editColumns(): void {
    this.hideShowColumns = !this.hideShowColumns;
  }

  //toggles the headerIndex Map based on the switch
  setHeaders(header): void {
    this.headerIndexMap.set(this.headers.indexOf(header), !this.headerIndexMap.get(this.headers.indexOf(header)));
  }

  //returns only the data that is to be shown
  filtered(item): any {
    return item.filter(oldItem => {
      if (item.indexOf(oldItem) < this.headerIndexMap.size && this.headerIndexMap.get(item.indexOf(oldItem))) {
        return true;
      }
      return false;
    });
  }

  getPstTime(t) {
    let pstDate = t;
    if (Number(t)) {
      pstDate = this.commonService.convertEpochToDate(Number(t), this.TIMEZONE);
    }
    return this.commonService.getShortDate(pstDate);

  }
}

