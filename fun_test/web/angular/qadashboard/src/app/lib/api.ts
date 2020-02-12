import {ApiService} from "../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {of, throwError} from "rxjs";
import {LoggerService} from "../services/logger/logger.service";
import {AppInjector} from "../app-injector";

export abstract class Api {
  url: string = null;
  abstract classType: any = null;
  deserializationHooks = {};

  abstract serialize(): any;
  public deSerialize(data: any): any {
    Object.keys(data).forEach(key => {
      let value = this[key];
      if (this.deserializationHooks.hasOwnProperty(key)) {
        try {
          this[key] = this.deserializationHooks[key](data[key]);
        } catch (e) {
          this[key] = data[key];
        }
      } else {
        this[key] = data[key];
      }
    });
    return this;
  }
  private apiService: ApiService;
  private loggerService: LoggerService;

  constructor() {

    this.apiService = AppInjector.get(ApiService);
    this.loggerService =  AppInjector.get(LoggerService);
  }

  public create(url, payload) {
    return this.apiService.post(url, payload).pipe(switchMap(response => {
      this.deSerialize(response.data);
      return of(this);
    }), catchError(error => {
      this.loggerService.error(`Unable to create: ${this.constructor.name}`, error);
      return throwError(error);
    }))
  }

  public putOperation(url, payload, operation) {
    url = `${url}?operation_type=${operation}`;
    return this.apiService.put(url, payload).pipe(switchMap(response => {
      this.deSerialize(response.data);
      return of(this);
    }), catchError(error => {
      this.loggerService.error(`Unable to post operation: ${operation}`, error);
      return throwError(error);
    }))
  }

  public getUrl(params?) {
    let url = this.url;
    if (params && params.hasOwnProperty('execution_id')) {
      url = `${url}/${params.execution_id}`;
    }
    return url;
  }

  public get(url?) {
    if (!url) {
      url = this.url;
    }
    return this.apiService.get(url).pipe(switchMap(response => {
      this.deSerialize(response.data);
      return of(this);
    }), catchError(error => {
      this.loggerService.error(`Unable to get: ${this.constructor.name}`, error);
      return throwError(error);
    }))
  }

  public getAll() {
    return this.apiService.get(this.url).pipe(switchMap(response => {

      let allObjects = [];
      if (response.data) {
        allObjects = response.data.map(oneEntry => {
          let newInstance = new this.classType();
          newInstance.deSerialize(oneEntry);
          return newInstance;
        });
      }
      return of(allObjects);
    }), catchError(error => {
      this.loggerService.error(`Unable to getAll: ${this.constructor.name}`, error);
      return throwError(error);
    }))

  }

  public delete(url) {
    return this.apiService.delete(url).pipe(switchMap(response => {
      return of(null);
    }), catchError(error => {
      this.loggerService.error(`Unable to delete: ${this.constructor.name}`, error);
      return throwError(error);
    }))
  }

  public deleteAll() {
  }

  public update(url?) {
    if (!url) {
      url = this.url;
    }
    return this.apiService.put(url, this.serialize()).pipe(switchMap(response => {
      this.deSerialize(response.data);
      return of(this);
    }), catchError(error => {
      this.loggerService.error(`Unable to put: ${this.constructor.name}`, error);
      return throwError(error);
    }))
  }

}

export class ApiType {
  private apiService: ApiService;
  private loggerService: LoggerService;
  descriptionMap: {[code: number]: string} = {};
  url: string = null;

  constructor() {
    this.apiService = AppInjector.get(ApiService);
    this.loggerService = AppInjector.get(LoggerService);
  }


  public get(url: string) {
    this.url = url;
    return this.apiService.get(this.url).pipe(switchMap(response => {
      let data = response.data;
      let stringCodeMap = data["string_code_map"];
      let descriptionMap = data["code_description_map"];
      Object.keys(stringCodeMap).forEach(key => this[key] = stringCodeMap[key]);
      Object.keys(descriptionMap).forEach(key => this.descriptionMap[key] = descriptionMap[key]);
      return of(this);
    }), catchError(error => {
      this.loggerService.error(`Unable to get ApiType: ${this.url}`, error);
      return throwError(error);
    }))
  }
}
