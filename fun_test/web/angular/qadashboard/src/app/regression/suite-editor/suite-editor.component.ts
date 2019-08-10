import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup} from "@angular/forms";

@Component({
  selector: 'app-suite-editor',
  templateUrl: './suite-editor.component.html',
  styleUrls: ['./suite-editor.component.css']
})
export class SuiteEditorComponent implements OnInit {
  newTaskForm = new FormGroup({
    name: new FormControl(''),
    category: new FormControl(''),
  });

  constructor() {
  }

  ngOnInit() {
  }

}
