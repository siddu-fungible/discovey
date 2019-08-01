import {Component, OnInit} from '@angular/core';
import {FormBuilder, Validators} from "@angular/forms";
import {LoggerService} from "../../services/logger/logger.service";
import {ApiService} from "../../services/api/api.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";
import {NgbModal, ModalDismissReasons} from '@ng-bootstrap/ng-bootstrap';
import {Title} from "@angular/platform-browser";

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
  closeResult: string = null;
  description: string = null;
  deletingWorkspace: any  = null;

  constructor(private loggerService: LoggerService, private  apiService: ApiService, private router: Router,
              private route: ActivatedRoute, private commonService: CommonService, private modalService: NgbModal, private title: Title) {
  }

  openAddWorkspace(content) {
    this.modalService.open(content, {ariaLabelledBy: 'modal-add-workspace'}).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
      this.modalService.dismissAll();

    }, (reason) => {
      this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    });
  }

  openEditWorkspace(content, workspace) {
    this.currentWorkspace = workspace;
    this.modalService.open(content, {ariaLabelledBy: 'modal-edit-workspace', size: 'lg'}).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
      // this.modalService.dismissAll();
    }, (reason) => {
      this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
      this.fetchWorkspaceAfterEditing();
    });
  }

  openDeleteWorkspace(content, workspace) {
    this.deletingWorkspace = workspace;
    this.modalService.open(content, {ariaLabelledBy: 'modal-delete-workspace'}).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
      this.fetchWorkspaceAfterEditing();
    });
  }


  private getDismissReason(reason: any): string {
    if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return `with: ${reason}`;
    }
  }

  ngOnInit() {
    this.title.setTitle('Workspace');
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

  deleteMetricInWorkspace(metricId): void {
    Object.keys(this.currentWorkspace.interestedMetrics[0]).forEach(key => {
      if (Number(key) === Number(metricId)) {
        delete this.currentWorkspace.interestedMetrics[0][key];
      }
    });
  }

  onDeleteWorkspace(workspace) {
    this.apiService.delete("/api/v1/profile/" + this.selectedUser.email + "/" + workspace.name).subscribe(response => {
      this.loggerService.success(`Deleted ${this.selectedUser.email} ${workspace.name}`);
      this.fetchWorkspaceAfterEditing();
      this.modalService.dismissAll();
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
        this.description = null;
        this.modalService.dismissAll();
      }, error => {
        this.addingWorkspace = false;
        this.workspaceName = null;
        this.description = null;
        this.loggerService.error("Unable to fetch workspace after creating");
      });
    } else if (this.createError === null) {
      this.createError = "Workspace name already taken. Please choose a different one"
    }
  }

  updateStatus(submitted, workspace): void {
    if (submitted) {
      workspace.editingWorkspace = false;
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
      // if (this.currentWorkspace) {
      //   this.openWorkspace(this.currentWorkspace);
      // }
    }, error => {
      this.loggerService.error("Unable to fetch workspace after editing");
    });
  }

  fetchWorkspace(user): any {
    return this.apiService.get("/api/v1/profile/" + user.email).pipe(switchMap(response => {
      let profiles = response.data;
      this.profile = [];
      for (let workspace of profiles.workspace) {
        let newWorkspace = {};
        newWorkspace["name"] = workspace.name;
        newWorkspace["description"] = workspace.description;
        newWorkspace["interestedMetrics"] = workspace.interested_metrics;
        newWorkspace["editingWorkspace"] = false;
        if (this.currentWorkspace && this.currentWorkspace.name === newWorkspace["name"]) {
          this.currentWorkspace.interestedMetrics = newWorkspace["interestedMetrics"];
        }
        this.profile.push(newWorkspace);
      }
      this.showWorkspace = true;
      return of(true);
    }));
  }

  submitWorkspace(): any {
    let payload = {};
    payload["email"] = this.selectedUser.email;
    let workspace = {};
    workspace["name"] = this.workspaceName;
    workspace["description"] = this.description;
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
    this.grids = [...workspace["interestedMetrics"]];
  }

  getString(dict): string {
    return JSON.stringify(dict);
  }

  editWorkspace(workspace): void {
    this.currentWorkspace = workspace;
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

  onChangeSubscribeTo(subscribed, metricId): void {
    Object.keys(this.currentWorkspace.interestedMetrics[0]).forEach(key => {
      if (Number(key) === Number(metricId)) {
        this.currentWorkspace.interestedMetrics[0][key]["subscribe"] = subscribed;
      }
    });
  }

  onChangeTrack(tracking, metricId): void {
    Object.keys(this.currentWorkspace.interestedMetrics[0]).forEach(key => {
      if (Number(key) === Number(metricId)) {
        this.currentWorkspace.interestedMetrics[0][key]["track"] = tracking;
      }
    });
  }

  saveWorkspace(): void {
    console.log("hello");
    let payload = {};
    payload["email"] = this.selectedUser.email;
    payload["workspace_name"] = this.currentWorkspace.name;
    payload["description"] = this.currentWorkspace.description;
    payload["interested_metrics"] = this.currentWorkspace.interestedMetrics;
    this.apiService.post("/api/v1/profile/edit_workspace/" + this.selectedUser.email, payload).subscribe(response => {
      this.loggerService.success(`Edited ${this.selectedUser.email} ${this.currentWorkspace.name}`);
      this.fetchWorkspaceAfterEditing();
    }, error => {
      this.loggerService.error(`Edit failed for ${this.selectedUser.email} ${this.currentWorkspace.name}`);
    });
  }

}
