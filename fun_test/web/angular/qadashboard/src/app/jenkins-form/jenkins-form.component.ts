import {Component, EventEmitter, Input, OnChanges, OnInit, Output} from '@angular/core';
import {FormBuilder, Validators} from "@angular/forms";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {TriageService} from "../regression/triage2/triage.service";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'app-jenkins-form',
  templateUrl: './jenkins-form.component.html',
  styleUrls: ['./jenkins-form.component.css']
})
export class JenkinsFormComponent implements OnInit, OnChanges {
  @Output() data: EventEmitter<number> = new EventEmitter();
  @Input() triagingType: number = null;
  submissionForm: any = null;
  jenkinsParameters: any = {};
  triageTypes: any = null;

  constructor(private formBuilder: FormBuilder, private triageService: TriageService, private loggerService: LoggerService) {
  }

  ngOnInit() {
    new Observable(observer => {
      observer.next(true);
      return () => {
      }
    }).pipe(switchMap(() => {
      return this.triageService.getTriageTypes();
    })).pipe(switchMap((triageTypes) => {
      this.triageTypes = triageTypes;
      return of(true);
    })).pipe(switchMap(() => {
      this.initializeForm();
      return of(true);
    }))
      .subscribe(() => {
      }, error => {
        this.loggerService.error("Jenkins component" + error);
      });

  }

  ngOnChanges() {
    this.initializeForm();
  }

  initializeForm(): void {
     this.createFormBuilder();

      if (this.submissionForm) {
        this.submissionForm.valueChanges.subscribe(value => {
          if (this.triagingType && Number(this.triagingType) !== this.triageTypes.JENKINS_FUN_OS_ON_DEMAND) {
            this.jenkinsParameters['BOOTARGS'] = value.BOOTARGS;
            this.jenkinsParameters['SKIP_DASM_C'] = value.SKIP_DASM_C;
            this.jenkinsParameters['MAX_DURATION'] = value.MAX_DURATION;
            this.jenkinsParameters['FUNOS_MAKEFLAGS'] = value.FUNOS_MAKEFLAGS;
            this.jenkinsParameters['DISABLE_ASSERTIONS'] = value.DISABLE_ASSERTIONS;
            this.jenkinsParameters['RELEASE_BUILD'] = value.RELEASE_BUILD;
            this.jenkinsParameters['HW_MODEL'] = value.HW_MODEL;
            this.jenkinsParameters['PCI_MODE'] = value.PCI_MODE;
            this.jenkinsParameters['REMOTE_SCRIPT'] = value.REMOTE_SCRIPT;
            this.jenkinsParameters['HW_VERSION'] = value.HW_VERSION;
          } else {
            this.jenkinsParameters['TEST_SCRIPT'] = value.TEST_SCRIPT;
            this.jenkinsParameters['TEST_SCRIPT_LOOP'] = value.TEST_SCRIPT_LOOP;
          }

          //console.log(this.jenkinsParameters);
          if (this.submissionForm.valid) {
            this.data.emit(this.jenkinsParameters);
          } else {
            this.data.emit(null);
          }
        });
      }
  }

  createFormBuilder() {
    if (this.triagingType && Number(this.triagingType) !== this.triageTypes.JENKINS_FUN_OS_ON_DEMAND) {
      this.submissionForm = this.formBuilder.group({
        'BOOTARGS': [null, Validators.required],
        'MAX_DURATION': [5],
        'SKIP_DASM_C': [true],
        'DISABLE_ASSERTIONS': [true],
        'RELEASE_BUILD': [true],
        'FUNOS_MAKEFLAGS': [''],
        'HW_MODEL': [''],
        'PCI_MODE': [''],
        'REMOTE_SCRIPT': [''],
        'HW_VERSION': ['Ignored']
      });
    } else if (this.triagingType && Number(this.triagingType) === this.triageTypes.JENKINS_FUN_OS_ON_DEMAND) {
      this.submissionForm = this.formBuilder.group({
        'TEST_SCRIPT': [null, Validators.required],
        'TEST_SCRIPT_LOOP': [1],
      });
    }
    if (this.triagingType && this.submissionForm.valid) {
      this.data.emit(this.jenkinsParameters);
    } else {
      this.data.emit(null);
    }
  }

}
