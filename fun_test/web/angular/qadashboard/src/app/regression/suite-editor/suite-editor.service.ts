import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";

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
  name: string;
  categories: string[];
  short_description: string;
  tags: string[];
  custom_test_bed_spec: any;
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

  constructor(private apiService: ApiService) { }

  suites() {

  }

  add(suite: SuiteInterface) {

  }


}
