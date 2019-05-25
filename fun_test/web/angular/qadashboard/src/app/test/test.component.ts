import {Component, OnInit, Input, OnChanges, Output, EventEmitter} from '@angular/core';
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


  constructor(private apiService: ApiService, private logger: LoggerService) {
  }

  ngOnInit() {

  }

}
