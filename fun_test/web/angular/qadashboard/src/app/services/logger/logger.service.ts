import { Injectable } from '@angular/core';


export let isDebugMode = true;
const noop = (): any => undefined;

@Injectable()
export class LoggerService {

  error(args: any) {

    let stack = (new Error).stack;
    //console.error.bind(console, arguments);
    console.error(stack + args);
  }

}
