import {Component, OnInit} from '@angular/core';
import {FormBuilder, Validators} from "@angular/forms";
import {LoggerService} from "../../services/logger/logger.service";
import {ApiService} from "../../services/api/api.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";

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
  showChartsForWorkspace: boolean = false;
  grids: any = [];
  gridLength: number = 0;
  createError: string = null;
  currentWorkspace: any = null;
  buildInfo: any = null;

  constructor(private loggerService: LoggerService, private  apiService: ApiService, private router: Router, private route: ActivatedRoute, private commonService: CommonService) {
  }

  ngOnInit() {
    this.fetchBuildInfo();
    this.route.params.subscribe(params => {
      if (params['emailId']) {
        let user = {};
        user["email"] = params["emailId"];
        this.fetchUsersWorkspace(user);
      }
    });
    this.workspaceName = null;
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchUsers();
      })).subscribe(response => {
      console.log("fetched users");
    }, error => {
      this.loggerService.error("Unable to fetch users");
    });
  }

  //populates buildInfo
  fetchBuildInfo(): void {
    this.apiService.get('/regression/build_to_date_map').subscribe((response) => {
      this.buildInfo = {};
      Object.keys(response.data).forEach((key) => {
        let localizedKey = this.commonService.convertToLocalTimezone(key);
        this.buildInfo[this.commonService.addLeadingZeroesToDate(localizedKey)] = response.data[key];
      });
    }, error => {
      this.loggerService.error("regression/build_to_date_map");
    });
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

  onDeleteWorkspace(workspace) {
    this.apiService.delete("/api/v1/profile/" + this.selectedUser.email + "/" + workspace.name).subscribe(response => {
      this.loggerService.success(`Deleted ${this.selectedUser.email} ${workspace.name}`);
      this.fetchWorkspaceAfterEditing();
    }, error => {
      this.loggerService.error(`Delete failed for ${this.selectedUser.email} ${workspace.name}`);
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
    let url = "/performance/workspace/" + newUser.email;
    this.router.navigateByUrl(url);
  }

  fetchWorkspace(user): any {
    return this.apiService.get("/api/v1/profile/" + user.email).pipe(switchMap(response => {
      let profiles = response.data;
      this.profile = [];
      for (let workspace of profiles.workspace) {
        // Object.keys(workspace).forEach(name => {
        let newWorkspace = {};
        newWorkspace["name"] = workspace.name;
        newWorkspace["interestedMetrics"] = workspace.interested_metrics;
        newWorkspace["editingWorkspace"] = false;
        if (this.currentWorkspace && this.currentWorkspace.name === newWorkspace["name"]) {
          this.currentWorkspace.interstedMetrics = newWorkspace["interestedMetrics"]

        }
        this.profile.push(newWorkspace);
        // });
      }
      this.showWorkspace = true;
      return of(true);
    }));
  }

  createWorkspace(): void {
    let error = false;
    if (this.workspaceName === null || this.workspaceName.trim() === "") {
      this.createError = "Enter some workspace name";
      error = true;
    } else {
      this.workspaceName = this.workspaceName.trim();
      for (let ws of this.profile) {
        if (ws.name == this.workspaceName) {
          error = true;
        }
      }
    }
    if (!error) {
      this.createError = null;
      new Observable(observer => {
        observer.next(true);
        observer.complete();
        return () => {
        }
      }).pipe(
        switchMap(response => {
          return this.submitWorkspace();
        }),
        switchMap(response => {
          return this.fetchWorkspace(this.selectedUser);
        })).subscribe(response => {
        console.log("fetched workspace after creating the workspace");
        this.addingWorkspace = false;
        this.workspaceName = null;
      }, error => {
        this.addingWorkspace = false;
        this.workspaceName = null;
        this.loggerService.error("Unable to fetch workspace after creating");
      });
    } else if (this.createError === null) {
      this.createError = "Workspace name already taken. Please choose a different one"
    }
  }

  updateStatus(submitted, workspace): void {
    if (submitted) {
      this.addingWorkspace = false;
      this.grids = [];
      this.showChartsForWorkspace = false;
      this.fetchWorkspaceAfterEditing();
    }
  }

  fetchWorkspaceAfterEditing(): void {
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchWorkspace(this.selectedUser);
      })).subscribe(response => {
      console.log("fetched workspace after editing the workspace");
      if (this.currentWorkspace) {
        this.openWorkspace(this.currentWorkspace);
      }
    }, error => {
      this.loggerService.error("Unable to fetch workspace after editing");
    });
  }

  submitWorkspace(): any {
    let payload = {};
    payload["email"] = this.selectedUser.email;
    let workspace = {};
    workspace["name"] = this.workspaceName;
    workspace["interested_metrics"] = [];
    payload["workspace"] = workspace;
    return this.apiService.post("/api/v1/profile/", payload).pipe(switchMap(response => {
      console.log("created workspace name successfully");
      return of(true);
    }));
  }

  openWorkspace(workspace): void {
    this.showChartsForWorkspace = true;
    this.currentWorkspace = workspace;
    this.gridLength = 2;
    this.grids = [...workspace["interestedMetrics"]];
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
    this.createError = null;
  }


  // submitWorkspace(user): void {
  //   let payload = {};
  //   payload["email"] = user.email;
  //   payload["interested_metrics"] = user.interested_metrics;
  //   this.apiService.post("/api/v1/profile", payload).subscribe(response => {
  //     this.profile = response.data;
  //     this.showWorkspace = true;
  //   }, error => {
  //     this.loggerService.error("Unable to fetch users");
  //   });
  //   this.fetchWorkspace(user);
  //   this.editingWorkspace = false;
  // }
}
