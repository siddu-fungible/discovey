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
  users: any = null;
  profileForm = this.fb.group({
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    email: ['', Validators.required]
  });

  constructor(private fb: FormBuilder, private loggerService: LoggerService, private  apiService: ApiService) { }

  ngOnInit() {
    this.fetchUsers();
  }

  onSubmit() {
    console.log(this.firstName.value);
    let payload = {};
    payload["first_name"] = this.firstName.value;
    payload["last_name"] = this.lastName.value;
    payload["email"] = this.email.value;
    this.apiService.post("/api/v1/users", payload).subscribe((response) => {
      this.loggerService.success(`User ${response.data.email} added successfully`);
      this.profileForm.reset();
      this.fetchUsers();

    }, error => {
      this.loggerService.error(error.value.error_message);
    });
  }

  onDelete(user) {
    this.apiService.delete("/api/v1/users/" + user.id).subscribe(response => {
      this.loggerService.success(`Deleted ${user.first_name} ${user.last_name} ${user.email}`);
      this.fetchUsers();

    }, error => {
      this.loggerService.error(`Delete failed for ${user.first_name} ${user.last_name} ${user.email}`);
    })
  }

  fetchUsers (): void {
    this.apiService.get("/api/v1/users").subscribe(response => {
      this.users = response.data;
    })
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
