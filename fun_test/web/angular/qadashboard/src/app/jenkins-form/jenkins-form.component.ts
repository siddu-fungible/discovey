import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {FormBuilder, Validators} from "@angular/forms";

@Component({
  selector: 'app-jenkins-form',
  templateUrl: './jenkins-form.component.html',
  styleUrls: ['./jenkins-form.component.css']
})
export class JenkinsFormComponent implements OnInit {
  @Output() data: EventEmitter<number> = new EventEmitter();
  submissionForm: any = null;
  jenkinsParameters: any = {};
  constructor(private formBuilder: FormBuilder) { }

  ngOnInit() {
    this.createFormBuilder();
    this.submissionForm.valueChanges.subscribe(value => {
      this.jenkinsParameters['BOOTARGS'] = value.BOOTARGS;
      this.jenkinsParameters['SKIP_DASM_C'] = value.SKIP_DASM_C;
      this.jenkinsParameters['MAX_DURATION'] = value.MAX_DURATION;
      this.jenkinsParameters['FUNOS_MAKEFLAGS'] = value.FUNOS_MAKEFLAGS;
      this.jenkinsParameters['DISABLE_ASSERTIONS'] = value.DISABLE_ASSERTIONS;
      this.jenkinsParameters['HW_MODEL'] = value.HW_MODEL;
      this.jenkinsParameters['PCI_MODE'] = value.PCI_MODE;

      //console.log(this.jenkinsParameters);
      if (this.submissionForm.valid) {
        this.data.emit(this.jenkinsParameters);
      } else {
        this.data.emit(null);
      }
    })

  }

  createFormBuilder() {
    this.submissionForm = this.formBuilder.group({
      'BOOTARGS': [null, Validators.required],
      'MAX_DURATION': [5],
      'SKIP_DASM_C': [true],
      'DISABLE_ASSERTIONS': [true],
      'FUNOS_MAKEFLAGS': [''],
      'HW_MODEL': [''],
      'PCI_MODE': ['']
    });
    if (this.submissionForm.valid) {
      this.data.emit(this.jenkinsParameters);
    } else {
      this.data.emit(null);
    }
  }

}
