import { Component, OnInit } from '@angular/core';
import {Title} from "@angular/platform-browser";

@Component({
  selector: 'app-site-construction',
  templateUrl: './site-construction.component.html',
  styleUrls: ['./site-construction.component.css']
})
export class SiteConstructionComponent implements OnInit {

  constructor(private title: Title) { }

  ngOnInit() {
    this.title.setTitle("Site under Construction");
  }

}
