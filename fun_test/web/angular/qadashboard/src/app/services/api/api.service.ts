import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {catchError, map} from 'rxjs/operators';
import {Observable, of} from "rxjs";

export class ApiResponse {
  status: boolean;
  data: any;
  error_message: string;
  message: string;
  public constructor(
    fields?: {
      status?: boolean,
      data?: object,
      message?: string
  }) {
    if (fields) Object.assign(this, fields);
  }
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(private httpClient: HttpClient) {

  }

  private static handleError(error: HttpErrorResponse): Observable<ApiResponse> {
    let result: ApiResponse = new ApiResponse();
    result.status = false;
    result.data = null;
    result.error_message = `Http Error: Status: ${error.status} Text: ${error.statusText} URL: ${error.url}`; // TODO: Improve this
    throw of(result);

  }

  post(url: string, payload: any): Observable<ApiResponse> {
    return this.httpClient.post<ApiResponse>(url, payload)
      .pipe(
        map(response => {
          return response;
        }),
        catchError(ApiService.handleError)
      );
  }

  get(url: string): Observable<ApiResponse> {
    return this.httpClient.get<ApiResponse>(url)
      .pipe(
        map(response => {
          return response;
        }),
        catchError(ApiService.handleError)
      );
  }
}
