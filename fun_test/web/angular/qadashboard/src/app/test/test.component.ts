import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

class Node {
  uId: number;  // unique Id
  scriptPath: string;
  pk: number = null;
  childrenIds = null;
  indent: number = 0;
  show: boolean = false;
  expanded: boolean = false;
  leaf: boolean = false;
}

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})
export class TestComponent implements OnInit {
  tooltipContent = "";

  constructor(private apiService: ApiService, private logger: LoggerService, private renderer: Renderer2) {
  }

  ngOnInit() {
    /*
    this.tooltipContent = this.renderer.createElement("span");
    const text = this.renderer.createText("ABCCCC");
    this.renderer.appendChild(this.tooltipContent, text);
    let s = 0;*/

  }

  tooltipCallback() {
    let content = this.renderer.createElement("span");

    for (let i = 0; i <100; i++) {
      const text = this.renderer.createText("From callback");
      this.renderer.appendChild(content, text);
    }

    let href = this.renderer.createElement('a');
    this.renderer.appendChild(href, this.renderer.createText('link'));
    this.renderer.setProperty(href, "href", "http://www.google.com");
    this.renderer.appendChild(content, href);
    return content;
  }

}
