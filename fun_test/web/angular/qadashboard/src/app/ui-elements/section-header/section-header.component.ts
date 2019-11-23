import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-section-header',
  templateUrl: './section-header.component.html',
  styleUrls: ['./section-header.component.css']
})
export class SectionHeaderComponent implements OnInit {
  @Input() value: string;
  constructor() { }

  ngOnInit() {
  }

}
