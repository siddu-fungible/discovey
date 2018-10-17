import { Component, OnInit } from '@angular/core';
import {PagerService} from "../services/pager/pager.service";
import {ApiService} from "../services/api/api.service";

@Component({
  selector: 'app-regression',
  templateUrl: './regression.component.html',
  styleUrls: ['./regression.component.css']
})
export class RegressionComponent implements OnInit {
pager: any;
suiteExecutionsCount: number;
recordsPerPage: number;
tags: string;
filterString: string;
items: any;

  constructor(private pagerService: PagerService, private apiService: ApiService) { }

  ngOnInit() {
  }

  setPage(page) {
        this.pager = this.pagerService.getPager(this.suiteExecutionsCount, page, this.recordsPerPage);
        if (page === 0 || (page > this.pager.endPage)) {
            return;
        }
        let payload = {};
        if(this.tags !== null) {
            payload["tags"] = this.tags;
        }
        this.apiService.post("/regression/suite_executions/" + this.recordsPerPage + "/" + page + "/" + this.filterString, payload)._subscribe(result => {
            this.items = result.data;
        });
    }

}
