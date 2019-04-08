import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup} from '@angular/forms';

@Component({
  selector: 'app-workflow1-stage2',
  templateUrl: './workflow1-stage2.component.html',
  styleUrls: ['./workflow1-stage2.component.css']
})
export class Workflow1Stage2Component implements OnInit {

  options: FormGroup;

  constructor(fb: FormBuilder) {
    this.options = fb.group({
      hideRequired: false,
      floatLabel: 'auto',
    });
  }

  ngOnInit() {
  }

}
