import { Injectable } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {from, of} from "rxjs";
import {switchMap} from "rxjs/operators";

enum TriagingStates {
  UNKNOWN = -100,
  ERROR = -99,
  KILLED = -30,
  ABORTED = -20,
  COMPLETED = 10,
  INIT = 20,
  IN_PROGRESS = 60,
  SUSPENDED = 70

}
@Injectable({
  providedIn: 'root'
})
export class TriageService {
  triagingStateMap: any = null;
  triagingTrialStateMap: any = null;
  constructor(private apiService: ApiService) { }

  triagingStateToString() {
    let url = "/api/v1/triage_states";
    if (!this.triagingStateMap) {
      return this.apiService.get(url).pipe(switchMap((response) => {
        return of(response.data);
      }));
    } else {
      return of(this.triagingStateMap);
    }
  }

  triagingTrialStateToString() {
    let url = "/api/v1/triaging_trial_states";
    if (!this.triagingTrialStateMap) {
      return this.apiService.get(url).pipe(switchMap((response) => {
        return of(response.data);
      }));
    } else {
      return of(this.triagingTrialStateMap);
    }
  }

  triages(triageId) {
    let url = "/api/v1/triages";
    if (triageId) {
      url += "/" + triageId;
    }
    return this.apiService.get(url).pipe(switchMap((response) => {
      return of(response.data);
    }))
  }

  add(triageType,
      regexMatchString=null,
      fromFunOsSha=null,
      toFunOsSha=null,
      submitterEmail=null,
      buildParameters=null) {
    let payload = {};
    payload["triage_type"] = triageType;
    if (regexMatchString) {
      payload["regex_match_string"] = regexMatchString;
    }
    if (fromFunOsSha) {
      payload["from_fun_os_sha"] = fromFunOsSha;
    }
    if (toFunOsSha) {
      payload["to_fun_os_sha"] = toFunOsSha;
    }
    if (submitterEmail) {
      payload["submitter_email"] = submitterEmail;
    }

    if (buildParameters) {
      payload["build_parameters"] = buildParameters;
    }
    let url = "/api/v1/triages";
    return this.apiService.post(url, payload).pipe(switchMap((response) => {
      return of(response.data);
    }));
  }

  trials(triageId, funOsSha) {
    let url = "/api/v1/triages/" + triageId + "/trials";
    return this.apiService.get(url).pipe(switchMap((response) => {
      return of(response.data);
    }));
  }

  funOsCommits(fromSha, toSha) {
    let url = "/api/v1/git_commits_fun_os/" + fromSha + '/' + toSha;
    return this.apiService.get(url).pipe(switchMap((response) => {
      return of(response.data);
    }))
  }

  getTriageTypes() {
    let url = "/api/v1/triage_types";
    return this.apiService.get(url).pipe(switchMap((response) => {
      return of(response.data);
    }))
  }


  stopTriage(triageId) {
    let url = "/api/v1/triages/" + triageId;
    let payload = {"status": TriagingStates.COMPLETED};
    return this.apiService.post(url, payload);
  }




}
