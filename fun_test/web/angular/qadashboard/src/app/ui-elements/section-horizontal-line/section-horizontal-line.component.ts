import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-section-horizontal-line',
  templateUrl: './section-horizontal-line.component.html',
  styleUrls: ['./section-horizontal-line.component.css']
})
export class SectionHorizontalLineComponent implements OnInit {
  @Input() text: string;
  constructor() { }

  ngOnInit() {
  }

}
