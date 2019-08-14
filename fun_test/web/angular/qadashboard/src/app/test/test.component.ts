import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";
import {RegressionService} from "../regression/regression.service";
import {FormControl, FormGroup} from "@angular/forms";
import { FormBuilder, Validators} from "@angular/forms";

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})

export class TestComponent implements OnInit {
  //form model
  // registrationForm = new FormGroup({
  //   userName: new FormControl('Rohan'),
  //   password: new FormControl(''),
  //   confirmPassword: new FormControl('')
  // });

  registrationForm = this.fb.group({
    userName: ['Rohan'],
    password: [''],
    confirmPassword: ['']
  })


  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService, private regressionService: RegressionService,
              private fb: FormBuilder) {
  }


  ngOnInit() {

  }

  loadApiData() {
    this.registrationForm.setValue({
      userName: 'Bob',
      password: 'fun123',
      confirmPassword: 'fun123'
    });
  }


}




