import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse, HttpHeaders} from '@angular/common/http';
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

  private static handleError(error: any): Observable<ApiResponse> {
    let result: ApiResponse = new ApiResponse();
    result.status = false;
    result.data = null;
    if (error.hasOwnProperty('statusText')) {
      result.error_message = `Http Error: Status: ${error.status} Text: ${error.statusText} URL: ${error.url}`; // TODO: Improve this
    } else {
      result.error_message = error.error_message;
    }
    throw of(result);
  }
  private static handleApiError(apiResponse: ApiResponse): Observable<ApiResponse> {
    throw of(apiResponse);
  }

  post(url: string, payload: any): Observable<ApiResponse> {
    return this.httpClient.post<ApiResponse>(url, payload)
      .pipe(
        map(response => {
          if (!response.status) {
            throw response;
          } else {
            return response;
          }
        }),
        catchError(ApiService.handleError)
      );
  }

  get(url: string): Observable<ApiResponse> {
    const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json',
    'Access-Control-Allow-Origin': '*'
  })};
    return this.httpClient.get<ApiResponse>(url, httpOptions)
      .pipe(
        map(response => {

          if (!response.status) {
            throw response;
          } else {
            return response;
          }
        }),
        catchError(ApiService.handleError)
      );
  }
}
