import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-ul-error-panel',
  templateUrl: './ul-error-panel.component.html',
  styleUrls: ['./ul-error-panel.component.css']
})
export class UlErrorPanelComponent implements OnInit {
  @Input() messages: string [] = [];
  constructor() { }

  ngOnInit() {
  }

}
