import { Component, OnInit } from '@angular/core';
import {SuiteEditorService, Suite} from "../suite-editor.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";


@Component({
  selector: 'app-suites-view',
  templateUrl: './suites-view.component.html',
  styleUrls: ['./suites-view.component.css']
})
export class SuitesViewComponent implements OnInit {

  constructor(private service: SuiteEditorService) { }
  suites: Suite[] = null;
  ngOnInit() {
    of(true).pipe(switchMap(() => {
      return this.service.suites();
    })).subscribe(response => {
      this.suites = response;
    })
  }

}
