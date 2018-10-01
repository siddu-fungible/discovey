import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
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

@Component({
  selector: 'fun-table',
  templateUrl: './fun-table.component.html',
  styleUrls: ['./fun-table.component.css'],
  changeDetection: ChangeDetectionStrategy.Default
})

export class FunTableComponent implements OnInit {
  headers: any[];
  // originalHeaders: any[];
  rows: any[];
  // originalRows: any[];
  pageSize: number;
  hideShowColumns: boolean = false;
  headerIndexMap: Map<number, boolean> = new Map<number, boolean>();
  static readonly defaultPageSize: number = 10;

  constructor(private apiService: ApiService, private pagerService: PagerService, private logger: LoggerService, private changeDetector: ChangeDetectorRef) {
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
    // this.doSomething1();
  }

  //setting the page number
  setPage(page: number) {
    // get pager object from service
    if (!this.data.all) {
      this.nextPage.emit(page);
    } else {
      this.setPagedItems(page);
    }
  }

  //setting the rows to be displayed by the template
  setPagedItems(page: number) {
    this.pager = this.pagerService.getPager(this.data.totalLength, page, this.pageSize);
    if (this.data.all) {
      this.pagedItems = this.rows.slice(this.pager.startIndex, this.pager.endIndex + 1);
    } else {
      this.pagedItems = this.rows.slice(0, this.pageSize);
    }
  }

  ngOnChanges() {
    if (this.data.currentPageIndex < 0) {
      this.logger.fatal("Page Index is less than 1");
    } else {
      this.rows = this.data.rows;
      this.headers = this.data.headers;
      // this.originalHeaders = this.data.headers;
      // this.originalRows = this.data.rows;
      for (let i in this.headers) {
        this.headerIndexMap.set(Number(i), true);
      }
      // this.headerIndexMap.set(0, true);
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
    this.headerIndexMap.forEach((value, key) => {
      console.log(Number(key) ,this.headerIndexMap.get(Number(key)));
    });
    this.hideShowColumns = !this.hideShowColumns;
  }

  setHeaders(header) {
    // this.headerIndexMap.set(this.originalHeaders.indexOf(header), !this.headerIndexMap.get(this.originalHeaders.indexOf(header)));
    // let newHeaders = this.originalHeaders.filter(item => {
    //   if(this.headerIndexMap.get(this.originalHeaders.indexOf(item)) === true) {
    //     return true;
    //   }
    //   return false;
    // });
    // for (let i = 0; i < this.originalRows.length; i++) {
    //   this.rows[i] = this.originalRows[i].filter(item => {
    //   if(this.headerIndexMap.get(this.originalHeaders.indexOf(item)) === true) {
    //     return true;
    //   }
    //   return false;
    // });
    // }
    // this.headers = newHeaders;
    // // this.setPage(1);
    this.headerIndexMap.set(this.headers.indexOf(header), !this.headerIndexMap.get(this.headers.indexOf(header)));
    // this.filtered(this.headers);
    // this.changeDetector.detectChanges();
  }

  // filteredHeaders(indexMap) {
  //   console.log("filtered header");
  //   return this.headers.filter(item => {
  //           if(this.headers.indexOf(item) < indexMap.size && indexMap.get(this.headers.indexOf(item))) {
  //             return true;
  //           }
  //           return false;
  //       });
  // }

  filtered(item) {
    return item.filter(oldItem => {
            if(item.indexOf(oldItem) < this.headerIndexMap.size && this.headerIndexMap.get(item.indexOf(oldItem))) {
              return true;
            }
            return false;
        });
  }
    doSomething1(): void {
    console.log("Doing Something1");
    let payload = {"metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"]};
    this.apiService.post('/metrics/scores', payload).subscribe(response => {
        //console.log(response.data);

      },
      error => {
        //console.log(error);
        this.delay(1000)
        this.doSomething1();
      });

  }
  async delay(ms: number) {
    await new Promise(resolve => setTimeout(()=>resolve(), ms)).then(()=>console.log("fired"));
}
r() {
   return Math.random();
}

}

function compare(a, b, isAsc) {
  return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
}
