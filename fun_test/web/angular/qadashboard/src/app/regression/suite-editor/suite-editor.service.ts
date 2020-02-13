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
  id: number;
  name: string;
  categories: string[];
  short_description: string;
  tags: string[];
  custom_test_bed_spec: any;
  entries: SuiteEntry[];
  type: SuiteMode;
  selected: boolean;
  suite_owner: string;
}



export class Suite implements SuiteInterface {
  id: number = null;
  name: string = null;
  categories: string[] = null;
  short_description: string = null;
  tags: string[] = null;
  custom_test_bed_spec: any = null;
  entries: SuiteEntry[] = null;
  type: SuiteMode = SuiteMode.SUITE;
  selected: boolean = false;
  suite_owner: string = null;

  constructor(obj?: any) {
    Object.assign(this, obj);
  }

  p () {
    console.log("Hi");
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

  suites<T>(getCount=null, recordsPerPage=null, page=null, selectedCategories=null, byNameSearchText=null): Observable<T> {
    let url = "/api/v1/regression/suites";
    if (recordsPerPage) {
      url += `?records_per_page=${recordsPerPage}&page=${page}`;
    }
    if (getCount) {
      url += `&get_count=${getCount}`;
    }
    if (byNameSearchText) {
      url += `&search_by_name=${byNameSearchText}`;
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
      if (getCount) {
        return of(response.data);
      } else {
        //const array = JSON.parse(JSON.stringify(response.data)) as any[];
        const array = response.data;// as any[];
        const details = array.map(data => new Suite(data));
        return of(details);
      }
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
      url += `/${id}`;
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

  delete(suite: SuiteInterface) {
    return this.apiService.delete('/api/v1/regression/suites/' + suite.id).pipe(switchMap(response => {
      return of(true);
    }), catchError(error => {
      throw error;
    }))
  }

}
