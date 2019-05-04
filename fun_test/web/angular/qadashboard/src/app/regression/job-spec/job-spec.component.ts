import {Component, Input, OnInit} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'app-job-spec',
  templateUrl: './job-spec.component.html',
  styleUrls: ['./job-spec.component.css']
})
export class JobSpecComponent implements OnInit {
  @Input() id: number = null;
  queryParameters: any = null;

  constructor(private apiService: ApiService,
              private route: ActivatedRoute) { }

  ngOnInit() {
    of(1).pipe(switchMap(r => {
      return this.getQueryParam();
    }))
  }

  getQueryParam() {
    return this.route.queryParams.pipe(switchMap(params => {
      if (params.hasOwnProperty('id')) {
      }
      this.queryParameters = params;
      return of(params);
    }))
  }

}
