import {ApiService} from "../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {of, throwError} from "rxjs";
import {LoggerService} from "../services/logger/logger.service";
import {AppInjector} from "../app-injector";
//import {AppModule} from "../app.module";

export abstract class Api {
  abstract url: string = null;
  abstract classType: any = null;

  abstract serialize(): any;
  abstract deSerialize(data: any): any;
  private apiService: ApiService;
  private loggerService: LoggerService;

  constructor() {

    this.apiService = AppInjector.get(ApiService); //AppModule.injector.get(ApiService);
    this.loggerService =  AppInjector.get(LoggerService); //AppModule.injector.get(LoggerService);
  }

  public create(url, payload) {
    return this.apiService.post(this.url, payload).pipe(switchMap(response => {
      this.deSerialize(response.data);
      return of(this);
    }), catchError(error => {
      this.loggerService.error(`Unable to create: ${this.constructor.name}`, error);
      return throwError(error);
    }))
  }

  public get(url) {
    return this.apiService.get(this.url).pipe(switchMap(response => {
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
