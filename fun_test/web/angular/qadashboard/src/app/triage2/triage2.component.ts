import {Component, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {TriageService} from "./triage.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {UserService} from "../services/user/user.service";
import {FormBuilder, FormControl, FormGroup, Validators} from "@angular/forms";

@Component({
  selector: 'app-triage2',
  templateUrl: './triage2.component.html',
  styleUrls: ['./triage2.component.css']
})
export class Triage2Component implements OnInit {
  submissionForm: any = null;
  users: any = null;
  selectedUser: any = null;
  jenkinsParameters: any = null;
  triagingStateMap: any = null;
  triagingTrialStateMap: any = null;
  triages: any = null;

  constructor(private apiService: ApiService,
              private loggerService: LoggerService,
              private triageService: TriageService,
              private userService: UserService,
              private formBuilder: FormBuilder) {
    this.createFormBuilder();

  }

  createFormBuilder() {
    this.submissionForm = this.formBuilder.group({
      'submitter': [null, Validators.required],
      'from_fun_os_sha': [null, Validators.required],
      'to_fun_os_sha': [null, Validators.required],
      'metric_id': [null, Validators.required]
    });
  }


  createFormGroup() {
    return new FormGroup({
      submitter: new FormControl()
    })
  }


  ngOnInit() {
    new Observable(observer => {
      observer.next(true);
      return () => {
      }}).pipe(switchMap(() => {
        return this.userService.users();
      })).pipe(switchMap((users) => {
        this.users = users;
        return of(true);
      })).pipe(switchMap(() => {
        return this.triageService.triagingStateToString();
      })).pipe(switchMap((triagingStateMap) => {
        this.triagingStateMap = triagingStateMap;
        return this.triageService.triagingTrialStateToString();
      })).pipe(switchMap((triagingTrialStateMap) => {
        this.triagingTrialStateMap = triagingTrialStateMap;
        return of(true);
      })).pipe(switchMap(() => {
        return this.triageService.triages(null);
      })).pipe(switchMap((triages) => {
        this.triages = triages;
        return of(true);
      }))
      .subscribe(() => {

      }, error => {
        this.loggerService.error(error);
      })
  }

  onSubmit() {
    //alert(this.submissionForm.value.submitter);
    let payload = {};
    payload["metric_id"] = this.submissionForm.value.metric_id;
  }

  jenkinsParametersChanged(value) {
    this.jenkinsParameters = value;
  }

  getShortSha(sha) {
    return sha.substring(0, 7);
  }

}
