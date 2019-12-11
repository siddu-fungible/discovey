import {ApiService} from "../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {of, throwError} from "rxjs";
import {LoggerService} from "../services/logger/logger.service";
import {AppInjector} from "../app-injector";

export abstract class Api {
  abstract url: string = null;
  abstract classType: any = null;

  abstract serialize(): any;
  public deSerialize(data: any): any {
    Object.keys(data).forEach(key => {
      this[key] = data[key];
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

  public getUrl(params) {
    let url = this.url;
    if (params.hasOwnProperty('execution_id')) {
      url = `${url}/${params.execution_id}`;
    }
    return url;
  }

  public get(url) {
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
      let allObjects = response.data.map(oneEntry => {
        //let newInstance = new this.constructor();
        let newInstance = new this.classType();
        //newInstance.constructor.apply(newInstance, oneEntry);
        newInstance.deSerialize(oneEntry);
        return newInstance;
      });
      return of(allObjects);
    }), catchError(error => {
      this.loggerService.error(`Unable to getAll: ${this.constructor.name}`, error);
      return throwError(error);
    }))

  }

  public delete() {
  }

  public deleteAll() {
  }

  public update() {
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
