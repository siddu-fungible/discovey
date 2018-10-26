import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse, HttpHeaders, HttpResponse} from '@angular/common/http';
import {catchError, map, repeat} from 'rxjs/operators';
import {Observable, of} from "rxjs";
import { v4 as uuid } from 'uuid';


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

export enum HttpMethod {
  GET = "GET",
  POST = "POST",
  DELETE = "DELETE",
  PUT = "PUT"
}

export class ApiLog {
  method: HttpMethod;
  text: string;
  url: string;
  id: string;
  payload: any;
  response: ApiResponse;
  http_status_code: number = null;
  setResponse(http_status_code: number, response: ApiResponse) {
    this.response = response;
    this.http_status_code = http_status_code;
  }

}



@Injectable({
  providedIn: 'root'
})
export class ApiService {
  apiLogs: ApiLog[] = [];

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

  post(url: string, payload: any, log: boolean = true): Observable<any> {
    let newApiLog: ApiLog = null;

    if (log) {
      newApiLog = this.addApiLog(HttpMethod.POST, url, payload, "");
    }

    return this.httpClient.post<any>(url, payload, {observe : 'response'})
      .pipe(
        map((response) => {
          let httpStatus = response.status;
          //let o = JSON.parse(response.body);
          let newApiResponse: ApiResponse = new ApiResponse(response.body);
          if (log) {
            newApiLog.setResponse(response.status, newApiResponse);
          }
          if (!newApiResponse.status) {
            throw newApiResponse;
          } else {
            return newApiResponse;
          }
        }),
        catchError ((error: any) => {
            let result: ApiResponse = new ApiResponse();
            result.status = false;
            result.data = null;
            if (error.hasOwnProperty('statusText')) {
              result.error_message = `Http Error: Status: ${error.status} Text: ${error.statusText} URL: ${error.url}`; // TODO: Improve this
            } else {
              result.error_message = error.error_message;
            }
            if (log) {
              newApiLog.setResponse(error.status, result);
            }

            throw of(result);
          }
        //catchError(ApiService.handleError)
      ));
  }

  get(url: string, log: boolean = true): Observable<any> {
    let newApiLog: ApiLog = null;
    if (log) {
      newApiLog = this.addApiLog(HttpMethod.GET, url, null, "");
    }
    const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json',
    'Access-Control-Allow-Origin': '*'
  })};
    return this.httpClient.get<any>(url, {observe : 'response'})
      .pipe(
        map((response) => {
          let httpStatus = response.status;
          //let o = JSON.parse(response.body);
          let newApiResponse: ApiResponse = new ApiResponse(response.body);
          if (log) {
            newApiLog.setResponse(response.status, newApiResponse);
          }
          if (!newApiResponse.status) {
            throw newApiResponse;
          } else {
            return newApiResponse;
          }
        }),
        catchError ((error: any) => {
            let result: ApiResponse = new ApiResponse();
            result.status = false;
            result.data = null;
            if (error.hasOwnProperty('statusText')) {
              result.error_message = `Http Error: Status: ${error.status} Text: ${error.statusText} URL: ${error.url}`; // TODO: Improve this
            } else {
              result.error_message = error.error_message;
            }
            if (log) {
              newApiLog.setResponse(error.status, result);
            }

            throw of(result);
          }
        //catchError(ApiService.handleError)
      ));
  }

  addApiLog(method: HttpMethod, url: string, payload: any, message: string) {
    let newApiLog: ApiLog = new ApiLog();
    newApiLog.url = url;
    newApiLog.text = message;
    newApiLog.method = method;
    newApiLog.payload = payload;
    newApiLog.id = uuid();

    this.apiLogs.push(newApiLog);
    /*setTimeout(() => {
      this.addApiLog();
      }, 10000);*/

    return newApiLog;
  }

  getApiLogs() {
    return this.apiLogs;
  }



}
