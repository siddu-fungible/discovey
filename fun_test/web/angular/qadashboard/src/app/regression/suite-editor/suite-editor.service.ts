import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {catchError, switchMap} from "rxjs/operators";
import {Observable, of} from "rxjs";

interface SuiteEntryInterface {
  script_path: string;
  inputs: string[];
  test_case_ids: number[];
}

interface SuiteInterface {
  name: string;
  categories: string[];
  short_description: string;
  tags: string[];
  custom_test_bed_spec: any;
  entries: SuiteEntry[];
}



export class Suite implements SuiteInterface {
  name: string = null;
  categories: string[] = null;
  short_description: string = null;
  tags: string[] = null;
  custom_test_bed_spec: any = null;
  entries: SuiteEntry[] = null;

  addEntry(suiteEntry: SuiteEntry) {
    if (!this.entries) {
      this.entries = [];
    }
    this.entries.push(suiteEntry);
  }
}

export class SuiteEntry implements SuiteEntryInterface {
  script_path: string;
  inputs: string[];
  test_case_ids: number[];
}

@Injectable({
  providedIn: 'root'
})
export class SuiteEditorService {

  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

  suites(id=null) {
    let url = "/api/v1/regression/suites";
    if (id) {
      url += `${id}`;
    }
    return this.apiService.get(url).pipe(switchMap(response => {
      return of(response.data);
    }), catchError(error => {
      throw error;
    }))
  }

  add(suite: SuiteInterface) {
    return this.apiService.post("/api/v1/regression/suites", suite).pipe(switchMap(response => {
      return of(true);

    }), catchError(error => {
      throw error;
    }))
  }

  replace(suite: SuiteInterface, id: number) {
    return this.apiService.post("/api/v1/regression/suites/" + id, suite).pipe(switchMap(response => {
      return of(true);

    }), catchError(error => {
      throw error;
    }))
  }


}
