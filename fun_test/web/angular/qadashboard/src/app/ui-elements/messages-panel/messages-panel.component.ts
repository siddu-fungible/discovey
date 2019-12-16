import {Component, Input, OnInit} from '@angular/core';

export class MessageTypes {
  static DANGER = "DANGER";
  static ERROR = "ERROR";
  static INFO = "INFO";
}

@Component({
  selector: 'app-messages-panel',
  templateUrl: './messages-panel.component.html',
  styleUrls: ['./messages-panel.component.css']
})
export class MessagesPanelComponent implements OnInit {
  MessageTypes = MessageTypes;
  @Input() messages: string [] = [];
  @Input() type: string = MessageTypes.INFO;
  constructor() {

  }

  ngOnInit() {
    if (this.type === MessageTypes.ERROR) {
      this.type = MessageTypes.DANGER;
    }

    if (this.type === MessageTypes.INFO) {
      this.type = MessageTypes.INFO;
    }
  }

}
