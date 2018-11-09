import {Component, Input, OnInit, Output, EventEmitter} from '@angular/core';

@Component({
  selector: 'cancel-btn-link',
  templateUrl: './btn-link.component.html',
  styleUrls: ['./btn-link.component.css']
})
export class CancelBtnLinkComponent implements OnInit {
@Input() text: string = "close";
@Input() prompt: boolean = false;
@Output() onClick = new EventEmitter();
  constructor() { }

  ngOnInit() {
  }

  buttonClose(): void {
    if (this.prompt) {
      if (confirm("Are you sure, you want to " + this.text)) {
        this.onClick.emit();
      }
    } else {
      this.onClick.emit();
    }
  }
}
