import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";
import {RegressionService} from "../regression/regression.service";
import {FormControl, FormGroup} from "@angular/forms";
import {FormBuilder, Validators} from "@angular/forms";
import {NgMultiSelectDropDownModule} from 'ng-multiselect-dropdown';
import {UserService} from "../services/user/user.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import { trigger, state, style, animate, transition } from '@angular/animations';



@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css'],
  animations: [
    trigger('fadeInOut', [
      state('void', style({
        opacity: 0
      })),
      transition('void <=> *', animate(500))
    ])
  ]
})

export class TestComponent {

  listItem = [];
  list_order: number = 1;

  addItem() {
    var listitem = "ListItem " + this.list_order;
    this.list_order++;
    this.listItem.push(listitem);
  }
  removeItem() {
    this.listItem.length -= 1;
  }
}
