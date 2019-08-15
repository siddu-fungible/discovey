import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {CommonService} from "../services/common/common.service";
import {RegressionService} from "../regression/regression.service";
import {FormControl, FormGroup} from "@angular/forms";
import {FormBuilder, Validators} from "@angular/forms";
import {NgMultiSelectDropDownModule} from 'ng-multiselect-dropdown';
import {UserService} from "../services/user/user.service";


@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})

export class TestComponent implements OnInit {
  //form model
  // registrationForm = new FormGroup({
  //   userName: new FormControl('Rohan'),
  //   password: new FormControl(''),
  //   confirmPassword: new FormControl('')
  // });

  registrationForm = this.fb.group({
    userName: ['Rohan'],
    password: [''],
    confirmPassword: ['']
  })


  constructor(private apiService: ApiService, private logger: LoggerService, private userService: UserService,
              private renderer: Renderer2, private commonService: CommonService, private regressionService: RegressionService,
              private fb: FormBuilder) {
  }


  dropdownList = [];
  selectedItems = [];
  dropdownSettings = {};
  userMap: any = null;
  submitter_emails : any = [];
  fetched : boolean = false;



  ngOnInit() {
    this.userService.getUserMap().subscribe((response) => {
      this.userMap = response;
      for (let user of Object.keys(this.userMap)){
        this.submitter_emails.push(user);
      }
      this.fetched = true;
    }, error => {
      this.logger.error("Unable to fetch usermap");
    });
    this.dropdownList = [
      {item_id: 1, item_text: 'Mumbai'},
      {item_id: 2, item_text: 'Bangaluru'},
      {item_id: 3, item_text: 'Pune'},
      {item_id: 4, item_text: 'Navsari'},
      {item_id: 5, item_text: 'New Delhi'}
    ];

    this.dropdownSettings = {
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      itemsShowLimit: 3,
      allowSearchFilter: true
    };
  }

  onItemSelect(item: any) {
    console.log(item);
  }

  onSelectAll(items: any) {
    console.log(items);
  }

}




