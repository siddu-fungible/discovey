import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {catchError, switchMap} from "rxjs/operators";
import {of} from "rxjs";

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

  suites() {

  }

  add(suite: SuiteInterface) {
    let payload = suite;
    return this.apiService.post("/api/v1/regression/suites", payload).pipe(switchMap(response => {
      return of(true);

    }), catchError(error => {
      throw error;
    }))
  }


}
