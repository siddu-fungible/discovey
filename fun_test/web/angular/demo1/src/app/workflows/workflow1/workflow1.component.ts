import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';

@Component({
  selector: 'app-workflow1',
  templateUrl: './workflow1.component.html',
  styleUrls: ['./workflow1.component.css']
})
export class Workflow1Component implements OnInit {
  currentStageIndex: number = 0;
  numStages: number = 2;
  isLinear = false;
  firstFormGroup: FormGroup;
  secondFormGroup: FormGroup;


  constructor(private _formBuilder: FormBuilder) {}

  ngOnInit() {
    this.firstFormGroup = this._formBuilder.group({
      firstCtrl: ['', Validators.required]
    });
    this.secondFormGroup = this._formBuilder.group({
      secondCtrl: ['', Validators.required]
    });
  }
  previousStage() {
    this.currentStageIndex--;
  }

  nextStage() {
    this.currentStageIndex++;
  }
}
