import {Component, OnInit} from '@angular/core';
import {FormBuilder, Validators} from "@angular/forms";
import {LoggerService} from "../../services/logger/logger.service";
import {ApiService} from "../../services/api/api.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";

@Component({
  selector: 'app-workspace',
  templateUrl: './workspace.component.html',
  styleUrls: ['./workspace.component.css']
})
export class WorkspaceComponent implements OnInit {
  users: any = null;
  selectedUser: any = null;
  showWorkspace: boolean = false;
  profile: any = null;
  editingWorkspace: boolean = false;
  addingWorkspace: boolean = false;
  workspaceName: string = null;

  constructor(private loggerService: LoggerService, private  apiService: ApiService, private router: Router, private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['emailId']) {
        let user = {};
        user["email"] = params["emailId"];
        this.fetchUsersWorkspace(user);
      }
    });
    this.workspaceName = null;
    this.fetchUsers();
  }

  fetchUsersWorkspace(user): void {
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchUsers();
      }),
      switchMap(response => {
        this.getSelectedUser(user);
        return of(true);
      }),
      switchMap(response => {
        return this.fetchWorkspace(user);
      })).subscribe(response => {
      console.log("fetched user and workspace from URL");
    }, error => {
      this.loggerService.error("Unable to initialize workspace");
    });
  }

  getSelectedUser(user): void {
    for (let select of this.users) {
      if (select.email === user.email) {
        this.selectedUser = select;
        break;
      }
    }
  }

  onDelete(user) {
    this.apiService.delete("/api/v1/users/" + user.id).subscribe(response => {
      this.loggerService.success(`Deleted ${user.first_name} ${user.last_name} ${user.email}`);
      this.fetchUsers();

    }, error => {
      this.loggerService.error(`Delete failed for ${user.first_name} ${user.last_name} ${user.email}`);
    })
  }

  fetchUsers(): any {
    return this.apiService.get("/api/v1/users").pipe(switchMap(response => {
      this.users = response.data;
      return of(true);
    }));
  }

  onUserChange(newUser): void {
    this.addingWorkspace = false;
    this.fetchWorkspace(newUser);
    let url = "/performance/workspace/" + newUser.email;
    this.router.navigateByUrl(url);
  }

  fetchWorkspace(user): any {
    return this.apiService.get("/api/v1/profile/" + user.email).pipe(switchMap(response => {
      let profiles = response.data;
      this.profile = [];
      for (let workspace of profiles.workspace) {
        Object.keys(workspace).forEach(name => {
          let newWorkspace = {};
          newWorkspace["name"] = name;
          newWorkspace["interestedMetrics"] = workspace[name];
          newWorkspace["editingWorkspace"] = false;
          this.profile.push(newWorkspace);
        });
      }
      this.showWorkspace = true;
      return of(true);
    }));
  }

  getString(dict): string {
    return JSON.stringify(dict);
  }

  editWorkspace(workspace): void {
    workspace.editingWorkspace = true;
  }

  addWorkspace(): void {
    this.addingWorkspace = true;
  }

  closeWorkspace(): void {
    this.addingWorkspace = false;
    this.workspaceName = null;
  }


  submitWorkspace(user): void {
    let payload = {};
    payload["email"] = user.email;
    payload["interested_metrics"] = user.interested_metrics;
    this.apiService.post("/api/v1/profile", payload).subscribe(response => {
      this.profile = response.data;
      this.showWorkspace = true;
    }, error => {
      this.loggerService.error("Unable to fetch users");
    });
    this.fetchWorkspace(user);
    this.editingWorkspace = false;
  }
}
