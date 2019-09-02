import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {catchError, switchMap, map} from "rxjs/operators";
import {Observable, of, throwError} from "rxjs";


export class SuiteMode {
  static SUITE = "SUITE";
  static TASK = "TASK";
}


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

  constructor(obj?: any) {
    Object.assign(this, obj);
  }

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

  suites(recordsPerPage=null, page=null, selectedCategories=null): Observable<Suite[]> {
    let url = "/api/v1/regression/suites";
    if (recordsPerPage) {
      url += `?records_per_page=${recordsPerPage}&page=${page}`;
    }
    if (selectedCategories && selectedCategories.length > 0) {
      let s = "";
      selectedCategories.forEach(selectedCategory => {
        s += selectedCategory + ","
      });
      s = s.replace(/,$/, '');
      url += `&categories=${s};`
    }

    return this.apiService.get(url).pipe(switchMap(response => {
      return of<Suite[]>(response.data);
    }))
  }

  suitesCount(): Observable<number> {
    let url = "/api/v1/regression/suites?get_count=true";
    return this.apiService.get(url).pipe(switchMap(response => {
      return of<number>(response.data);
    }))
  }

  suite(id=null): Observable<Suite>{
    let url = "/api/v1/regression/suites";
    if (id) {
      url += `${id}`;
    }

    return this.apiService.get(url).pipe(map(response => new Suite(response.data)));
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

  categories(): Observable<string []> {
    return of(["networking", "storage", "accelerators", "security", "system"]);
  }


}
