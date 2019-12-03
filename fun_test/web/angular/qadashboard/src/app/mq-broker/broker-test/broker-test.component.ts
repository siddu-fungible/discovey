import { Component, OnInit } from '@angular/core';
import {MqBrokerService} from "../mq-broker.service";
import {MqBrokerMessage} from "../definitions";
import {animate, animateChild, group, query, state, style, transition, trigger} from "@angular/animations";
import {slideInOutAnimation} from "../../animations/generic-animations";


class MyBrokerMessage implements MqBrokerMessage {
  message_type: number = 0;
  message: any = "abc";
  routing_key: string = "test";
}


@Component({
  selector: 'app-broker-test',
  templateUrl: './broker-test.component.html',
  styleUrls: ['./broker-test.component.css'], animations: [slideInOutAnimation]
})
export class BrokerTestComponent implements OnInit {
  brokerMessageTypes: any;
  someBoolean: boolean = true;
  constructor(private brokerService: MqBrokerService) { }

  ngOnInit() {
    this.brokerService.getMessageTypes().subscribe(response => {
      this.brokerMessageTypes = response;
      console.log(this.brokerMessageTypes.REGRESSION_CATALOG_EXECUTION);
    })
  }

  publish() {
    let brokerMessage = new MyBrokerMessage();
    this.brokerService.publish(brokerMessage).subscribe(response => {

    })
  }

  toggle() {
    this.someBoolean = !this.someBoolean;
  }
}
