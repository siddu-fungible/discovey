import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {TriageService} from "./triage.service";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {UserService} from "../../services/user/user.service";
import {FormBuilder, FormControl, FormGroup, Validators} from "@angular/forms";
import {Title} from "@angular/platform-browser";
import {UserProfile} from "../../login/definitions";
import {CommonService} from "../../services/common/common.service";


@Component({
  selector: 'app-triage2',
  templateUrl: './triage2.component.html',
  styleUrls: ['./triage2.component.css']
})
export class Triage2Component implements OnInit {
  submissionForm: any = null;
  users: any = null;
  jenkinsParameters: any = null;
  triagingStateMap: {[key: string]: number} = {};
  triagingStringToCodeMap = {};
  triagingTrialStateMap: any = null;
  triages: any = null;
  gitShasValid: boolean = false;
  commitsInBetween: any = null;
  validateShasStatus: string = null;
  triageTypes: any = null;
  userProfile: UserProfile = null;

  constructor(private apiService: ApiService,
              private loggerService: LoggerService,
              private triageService: TriageService,
              private userService: UserService,
              private formBuilder: FormBuilder,
              private title: Title,
              private commonService: CommonService) {
    this.createFormBuilder();

  }

  createFormBuilder() {
    this.submissionForm = this.formBuilder.group({
      'from_fun_os_sha': [null, Validators.required],
      'to_fun_os_sha': [null, Validators.required],
      'metric_id': [-1],
      'triage_type': [null, Validators.required],
      'regex_match_string': [null],
    });
    this.submissionForm.get('from_fun_os_sha').valueChanges.subscribe(value => {
      this.gitShasValid = false;
    });
    this.submissionForm.get('to_fun_os_sha').valueChanges.subscribe(value => {
      this.gitShasValid = false;
    });

    /*
    setInterval(() => {
      console.log(this.submissionForm.value.triage_type);
      console.log(this.triageTypes);
      console.log(this.triageTypes.REGEX_MATCH);
    }, 2000)*/
  }

  validateShas() {
    if ((!this.submissionForm.value.from_fun_os_sha)
      || (!this.submissionForm.value.to_fun_os_sha)
      || (this.submissionForm.value.from_fun_os_sha === "")
      || (this.submissionForm.value.to_fun_os_sha === "")) {
      return this.loggerService.error("Git commits are invalid");
    }
    let url = "/api/v1/git_commits_fun_os/" + this.submissionForm.value.from_fun_os_sha + "/" + this.submissionForm.value.to_fun_os_sha;
    this.validateShasStatus = "Validating commits";
    this.apiService.get(url).subscribe((response) => {
      this.commitsInBetween = response.data;
      if (this.commitsInBetween && this.commitsInBetween.length) {
        this.gitShasValid = true;
        this.validateShasStatus = null;

      }
    }, error => {
      this.loggerService.error("Git commits are invalid");
      this.validateShasStatus = null;

    })
  }

  createFormGroup() {
    return new FormGroup({
      submitter: new FormControl()
    })
  }


  ngOnInit() {
    this.title.setTitle("Regression Finder");
    this.userProfile = this.commonService.getUserProfile();
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
        for(let key of Object.keys(this.triagingStateMap)) {
          this.triagingStringToCodeMap[this.triagingStateMap[key]] = parseInt(key);
        }


        return this.triageService.triagingTrialStateToString();
      })).pipe(switchMap((triagingTrialStateMap) => {
        this.triagingTrialStateMap = triagingTrialStateMap;
        return this.triageService.getTriageTypes();
      })).pipe(switchMap((triageTypes) => {
        this.triageTypes = triageTypes;
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
    payload["from_fun_os_sha"] = this.submissionForm.value.from_fun_os_sha;
    payload["to_fun_os_sha"] = this.submissionForm.value.to_fun_os_sha;
    payload["submitter_email"] = this.userProfile.user.email;
    payload["triage_type"] = this.submissionForm.value.triage_type;
    payload["regex_match_string"] = this.submissionForm.value.regex_match_string;
    payload["build_parameters"] = this.jenkinsParameters;
    if (!this.jenkinsParameters) {
      return this.loggerService.error("Jenkins parameters are invalid");
    }
    let url = "/api/v1/triages";
    this.apiService.post(url, payload).subscribe((response) => {
      this.loggerService.success("Triage submitted");
      window.location.href = "/regression/triaging/" + response.data;
    },error => {
      this.loggerService.error("Submitting triage failed");
    });
    console.log(payload);
  }

  jenkinsParametersChanged(value) {
    this.jenkinsParameters = value;
  }

  getShortSha(sha) {
    return sha.substring(0, 7);
  }

  stopTriage(triageId) {
    this.triageService.stopTriage(triageId).subscribe((response) => {
      this.loggerService.success("Stop triage request sent");
      window.location.reload();
    }, error => {
      this.loggerService.error("Stop triage request failed");
    })
  }

}
