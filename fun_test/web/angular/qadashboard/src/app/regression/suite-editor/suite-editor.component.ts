import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup} from "@angular/forms";

class SuiteEntry {
  path: string;
  test_case_ids: number[] = null;
  inputs: any = null
}

@Component({
  selector: 'app-suite-editor',
  templateUrl: './suite-editor.component.html',
  styleUrls: ['./suite-editor.component.css']
})
export class SuiteEditorComponent implements OnInit {
  newSuiteEntryForm = new FormGroup({
    path: new FormControl(''),
    testCaseIds: new FormControl(''),
    inputs: new FormControl('')
  });

  constructor() {
  }

  ngOnInit() {
  }

}
