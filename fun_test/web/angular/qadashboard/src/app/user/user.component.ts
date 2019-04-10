import { Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Validators } from '@angular/forms';
import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";


@Component({
  selector: 'app-user',
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.css']
})
export class UserComponent implements OnInit {

  profileForm = this.fb.group({
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    email: ['', Validators.required]
  });

  constructor(private fb: FormBuilder, private loggerService: LoggerService, private  apiService: ApiService) { }

  ngOnInit() {
  }

  onSubmit() {
    console.log(this.firstName.value);
    let payload = {};
    payload["first_name"] = this.firstName.value;
    payload["last_name"] = this.lastName.value;
    payload["email"] = this.email.value;
    this.apiService.post("/api/v1/users", payload).subscribe((response) => {
      this.loggerService.success("User added successfully");
    }, error => {
      this.loggerService.error(error.value.error_message);
    });
  }

  get firstName() {
    return this.profileForm.get('firstName');
  }

  get lastName() {
    return this.profileForm.get('lastName');
  }

  get email() {
    return this.profileForm.get('email');
  }
}
