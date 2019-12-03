import { Component, OnInit } from '@angular/core';
import {MqBrokerService} from "../mq-broker.service";
import {MqBrokerMessage} from "../definitions";


class MyBrokerMessage implements MqBrokerMessage {
  message_type: number = 0;
  message: any = "abc";
  routing_key: string = "test";
}

@Component({
  selector: 'app-broker-test',
  templateUrl: './broker-test.component.html',
  styleUrls: ['./broker-test.component.css']
})
export class BrokerTestComponent implements OnInit {
  brokerMessageTypes: any;
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
}
