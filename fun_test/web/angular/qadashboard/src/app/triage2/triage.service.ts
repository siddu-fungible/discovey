import { Injectable } from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {of} from "rxjs";
import {switchMap} from "rxjs/operators";

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
}
