import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {catchError, map} from 'rxjs/operators';
import {Observable, of} from "rxjs";
import {LoggerService, Log, LogDataType, AlertLevel} from "../logger/logger.service";

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

class ApiLog {
  response: ApiResponse;
  method: string;
  url: string;
  payload?: any;

  public constructor(response: ApiResponse, method: string, url: string, payload?: any) {
    this.response = response;
    this.method = method;
    this.url = url;
    if (payload) {
      this.payload = payload;
    }
  }

}

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(private httpClient: HttpClient, private logger: LoggerService) {

  }

  //private handleError(error: any, url: string): Observable<ApiResponse> {
  private handleError(error: any, method: string, url: string, payload?: any): ApiResponse {

    let result: ApiResponse = new ApiResponse();
    result.status = false;
    result.data = null;
    if (error.hasOwnProperty('statusText')) {
      result.error_message = `Http Error: Status: ${error.status} Text: ${error.statusText} URL: ${error.url}\n`; // TODO: Improve this
      result.error_message += `Message: ${error.message}\n`;
      result.error_message += `Error.error.message: ${error.error.error.message}`;

    } else {
      result.error_message = error.error_message;
    }
    let apiLog = new ApiLog(result, method, url, payload);
    let newLog = new Log(null, apiLog, LogDataType.API, AlertLevel.ERROR);
    this.logger.addLog(newLog);
    //throw of(result);
    return result;
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
        catchError((error) => {
          throw of(this.handleError(error, "POST", url, payload))
        })
      );
  }

  get(url: string): Observable<ApiResponse> {
    return this.httpClient.get<ApiResponse>(url)
      .pipe(
        map(response => {
          if (!response.status) {
            throw response;
          } else {
            return response;
          }
        }),
        catchError((error) => {
          throw of(this.handleError(error, "GET",  url))
        })
      );
  }

  delete(url: string): Observable<ApiResponse> {
    return this.httpClient.delete<ApiResponse>(url)
      .pipe(
        map(response => {
          if (!response.status) {
            throw response;
          } else {
            return response;
          }
        }),
        catchError((error) => {
          throw of(this.handleError(error, "DELETE", url))
        })
      );
  }


}
