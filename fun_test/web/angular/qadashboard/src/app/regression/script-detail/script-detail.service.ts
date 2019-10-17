import { Injectable } from '@angular/core';
import {LoggerService} from "../../services/logger/logger.service";
import {ApiService} from "../../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {Observable, of, throwError} from "rxjs";


export class ContextInfo {
  date_time: string;
  context_id: number;
  description: string;
  suite_execution_id: number;
  test_case_execution_id: number;
  script_id: number;
  selected: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ScriptDetailService {

  constructor(private loggerService: LoggerService, private apiService: ApiService) { }

  getContexts(suiteExecutionId, scriptId): Observable<ContextInfo[]> {
    return this.apiService.get(`/api/v1/regression/contexts/${suiteExecutionId}/${scriptId}`).pipe(switchMap(response => {
      return of(response.data);
    }), catchError(error => {
      this.loggerService.error(`Unable to fetch contexts ${error}`);
      console.error(error);
      return throwError(error);
    }))
  }
}
