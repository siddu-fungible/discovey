import { Injectable } from '@angular/core';
import {ApiService} from "../api/api.service";
import {LoggerService} from "../logger/logger.service";
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class DaemonService {

  constructor(private apiService: ApiService, private loggerService: LoggerService) { }

  daemons () {

  }

  /*
  heartBeat (daemonName) {
    return new Observable(observer => {
      //observer.next(this.newAlert);
      setInterval(() => observer.next(this.newAlert), 1000);
      return () => {};
    })
  }*/


}
