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
import {PerformanceService} from "../performance.service";

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
  workspaceName: string = null;
  grids: any = [];
  gridLength: number = 0;
  createError: string = null;
  currentWorkspace: any = null;

  description: string = null;
  deletingWorkspace: any = null;

  constructor(private loggerService: LoggerService, private  apiService: ApiService, private router: Router,
              private route: ActivatedRoute, private commonService: CommonService, private modalService: NgbModal,
              private title: Title, private perfService: PerformanceService) {
  }

  ngOnInit() {
    this.title.setTitle('Workspace');
    this.route.params.subscribe(params => {
      if (params['emailId']) {
        let user = {};
        user["email"] = params["emailId"];
        this.fetchUsersWorkspaces(user);
      } else {
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
    });
    this.workspaceName = null;
  }

  openAddWorkspace(content) {
    this.modalService.open(content, {ariaLabelledBy: 'modal-add-workspace'}).result.then((result) => {
      this.modalService.dismissAll();

    }, (reason) => {
    });
  }

  openEditWorkspace(content, workspace) {
    this.currentWorkspace = workspace;
    this.modalService.open(content, {ariaLabelledBy: 'modal-edit-workspace', size: 'lg'}).result.then((result) => {
      // this.modalService.dismissAll();
    }, (reason) => {
      this.fetchWorkspacesAfterEditing();
    });
  }

  openDeleteWorkspace(content, workspace) {
    this.deletingWorkspace = workspace;
    this.modalService.open(content, {ariaLabelledBy: 'modal-delete-workspace'}).result.then((result) => {
      // this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      // this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
      this.fetchWorkspacesAfterEditing();
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

  getChartName(metricId, metricObject): string {
    let result = "";
    let payload = {};
    payload["metric_id"] = metricId;
    this.apiService.post("/metrics/chart_info", payload).subscribe((response) => {
      let chartInfo = response.data;
    },error => {
      this.loggerService.error("workspace-component: chart_info");
    });
    return result;
  }

  fetchUsers(): any {
    return this.apiService.get("/api/v1/users").pipe(switchMap(response => {
      this.users = response.data;
      return of(true);
    }));
  }

    onUserChange(newUser): void {
    let url = "/performance/workspace/" + newUser.email;
    this.router.navigateByUrl(url);
  }

  fetchUsersWorkspaces(user): void {
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
        return this.fetchWorkspaces(user);
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

  fetchWorkspaces(user): any {
    return this.apiService.get("/api/v1/workspaces/" + user.email).pipe(switchMap(response => {
      let workspaces = response.data;
      this.profile = [];
      if (workspaces.length) {
        for (let workspace of workspaces) {
        let newWorkspace = {};
        newWorkspace["name"] = workspace.workspace_name;
        newWorkspace["description"] = workspace.description;
        newWorkspace["interestedMetrics"] = workspace.interested_metrics;
        newWorkspace["editingWorkspace"] = false;
        newWorkspace["editingDescription"] = false;
        if (this.currentWorkspace && this.currentWorkspace.name === newWorkspace["name"]) {
          this.currentWorkspace.interestedMetrics = newWorkspace["interestedMetrics"];
        }
        this.profile.push(newWorkspace);
      }
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
          return this.fetchWorkspaces(this.selectedUser);
        })).subscribe(response => {
        console.log("fetched workspace after creating the workspace");
        this.workspaceName = null;
        this.description = null;
        this.modalService.dismissAll();
      }, error => {
        this.workspaceName = null;
        this.description = null;
        this.loggerService.error("Unable to fetch workspace after creating");
      });
    } else if (this.createError === null) {
      this.createError = "Workspace name already taken. Please choose a different one"
    }
  }

    fetchWorkspacesAfterEditing(): void {
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchWorkspaces(this.selectedUser);
      })).subscribe(response => {
      console.log("fetched workspace after editing the workspace");
      // if (this.currentWorkspace) {
      //   this.openWorkspace(this.currentWorkspace);
      // }
    }, error => {
      this.loggerService.error("Unable to fetch workspace after editing");
    });
  }

  submitWorkspace(): any {
    let payload = {};
    payload["email"] = this.selectedUser.email;
    payload["name"] = this.workspaceName;
    payload["description"] = this.description;
    return this.apiService.post("/api/v1/workspaces/", payload).pipe(switchMap(response => {
      console.log("created workspace name successfully");
      return of(true);
    }));
  }

  deleteMetricInWorkspace(metricId): void {
    Object.keys(this.currentWorkspace.interestedMetrics[0]).forEach(key => {
      if (Number(key) === Number(metricId)) {
        delete this.currentWorkspace.interestedMetrics[0][key];
      }
    });
  }

  onDeleteWorkspace(workspace) {
    this.apiService.delete("/api/v1/workspaces/" + this.selectedUser.email + "/" + workspace.name).subscribe(response => {
      this.loggerService.success(`Deleted ${this.selectedUser.email} ${workspace.name}`);
      this.fetchWorkspacesAfterEditing();
      this.modalService.dismissAll();
    }, error => {
      this.loggerService.error(`Delete failed for ${this.selectedUser.email} ${workspace.name}`);
    })
  }

  updateStatus(submitted, workspace): void {
    if (submitted) {
      workspace.editingWorkspace = false;
      this.grids = [];
      this.fetchWorkspacesAfterEditing();
    }
  }

  openWorkspace(workspace): void {
    this.currentWorkspace = workspace;
    this.grids = [...workspace["interestedMetrics"]];
    let url = "/performance/workspace/" + this.selectedUser.email + "/" + this.currentWorkspace.name;
    this.router.navigateByUrl(url);
  }

  getString(dict): string {
    return JSON.stringify(dict);
  }

  editWorkspace(workspace): void {
    this.currentWorkspace = workspace;
    workspace.editingWorkspace = true;
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
    payload["name"] = this.currentWorkspace.name;
    payload["description"] = this.currentWorkspace.description;
    payload["interested_metrics"] = this.currentWorkspace.interestedMetrics;
    this.apiService.post("/api/v1/workspaces/", payload).subscribe(response => {
      this.loggerService.success(`Edited ${this.selectedUser.email} ${this.currentWorkspace.name}`);
      this.fetchWorkspacesAfterEditing();
    }, error => {
      this.loggerService.error(`Edit failed for ${this.selectedUser.email} ${this.currentWorkspace.name}`);
    });
  }

}
