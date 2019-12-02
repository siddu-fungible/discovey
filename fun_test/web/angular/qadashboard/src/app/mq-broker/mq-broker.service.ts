import { Injectable } from '@angular/core';
import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {of, throwError} from "rxjs";
import {MqBrokerMessage} from "./definitions";

@Injectable({
  providedIn: 'root'
})
export class MqBrokerService {

  constructor(private loggerService: LoggerService, private apiService: ApiService) {
  }

  publish(brokerMessage: MqBrokerMessage) {
    let payload = {routing_key: brokerMessage.routing_key,
      message_type: brokerMessage.message_type,
      message: brokerMessage.message};
    let url = "/api/v1/mq_broker/publish";
    return this.apiService.post(url, payload).pipe(switchMap(response => {
      return of(true)
    }), catchError(error => {
      this.loggerService.error(`Unable to publish broker message`, error);
      return throwError(error);
    }))
  }
}
