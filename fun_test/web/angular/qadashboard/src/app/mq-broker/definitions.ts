import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";
import {catchError, switchMap} from "rxjs/operators";
import {of, throwError} from "rxjs";

export interface MqBrokerMessage {
  routing_key: string;
  message_type: number;
  message: any;
}

