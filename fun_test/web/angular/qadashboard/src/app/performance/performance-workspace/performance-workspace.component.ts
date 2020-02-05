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
import {SelectMode} from "../performance.service";
import {UserProfile} from "../../login/definitions";

@Component({
  selector: 'performance-workspace',
  templateUrl: './performance-workspace.component.html',
  styleUrls: ['./performance-workspace.component.css']
})
export class PerformanceWorkspaceComponent implements OnInit {
  users: any = null;
  selectedUser: any = null;
  showWorkspace: boolean = false;
  profile: any = null;
  editingWorkspace: boolean = false;
  gridLength: number = 0;
  createError: string = null;
  currentWorkspace: any = null;
  workspaceToBeDeleted: any = null;
  selectMode: any = SelectMode.ShowEditWorkspace;

  workspaceName: string = null;
  description: string = null;
  subscribeToAlerts: boolean = false;
  alertEmails: string = "";
  userProfile: UserProfile = null;

  constructor(private loggerService: LoggerService, private  apiService: ApiService, private router: Router,
              private route: ActivatedRoute, private commonService: CommonService, private modalService: NgbModal,
              private title: Title, private performanceService: PerformanceService) {
  }

  ngOnInit() {
    this.title.setTitle('Workspace');
    this.userProfile = this.commonService.getUserProfile();
    if (!this.userProfile) {
      this.loggerService.error("Unable to fetch user profile");
      return;
    }
    this.route.params.subscribe(params => {
      if (params['emailId']) {
        let user = {};
        user["email"] = params["emailId"];
        this.fetchUsersWorkspaces(user);
      } else {
        this.onUserChange(this.userProfile.user);
      }
    });
  }

  openAddWorkspace(content) {
    this.workspaceName = null;
    this.description = null;
    this.modalService.open(content, {ariaLabelledBy: 'modal-add-workspace'}).result.then((result) => {
      this.modalService.dismissAll();

    }, (reason) => {
    });
  }

  openEditWorkspace(content, workspace) {
    this.currentWorkspace = workspace;
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchInterestedMetrics(workspace.workspaceId);
      })).pipe(
      switchMap(response => {
        return this.modalService.open(content, {
          ariaLabelledBy: 'modal-edit-workspace',
          size: 'lg'
        }).result.then((result) => {
          // this.modalService.dismissAll();
        }, (reason) => {
          this.fetchWorkspacesAfterEditing();
        });
      })).subscribe(response => {
      console.log("opened edit modal");
    }, error => {
      this.loggerService.error("Unable to open edit modal");
    });
  }

  openDeleteWorkspace(content, workspace) {
    this.workspaceToBeDeleted = workspace;
    this.modalService.open(content, {ariaLabelledBy: 'modal-delete-workspace'}).result.then((result) => {
      // this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      // this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
      this.fetchWorkspacesAfterEditing();
    });
  }

  fetchInterestedMetrics(workspaceId): any {
    return this.apiService.get("/api/v1/performance/workspaces/" + workspaceId + "/interested_metrics").pipe(switchMap(response => {
      this.currentWorkspace["interestedMetrics"] = [];
      for (let metric of response.data) {
        this.currentWorkspace["interestedMetrics"].push(metric);
    }
      return of(true);
    }));
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
    }, error => {
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
    return this.apiService.get("/api/v1/performance/workspaces?email=" + user.email).pipe(switchMap(response => {
      let workspaces = response.data;
      this.profile = [];
      if (workspaces.length) {
        for (let workspace of workspaces) {
          let newWorkspace = {};
          newWorkspace["name"] = workspace.workspace_name;
          newWorkspace["description"] = workspace.description;
          newWorkspace["editingWorkspace"] = false;
          newWorkspace["editingDescription"] = false;
          newWorkspace["workspaceId"] = workspace.id;
          newWorkspace["subscribeToAlerts"] = workspace.subscribe_to_alerts;
          newWorkspace["alertEmails"] = workspace.alert_emails;
          newWorkspace["createdDate"] = workspace.date_created;
          newWorkspace["modifiedDate"] = workspace.date_modified;
          newWorkspace["editingAlerts"] = false;
          if (this.currentWorkspace && this.currentWorkspace.name === newWorkspace["name"]) {
            new Observable(observer => {
              observer.next(true);
              observer.complete();
              return () => {
              }
            }).pipe(
              switchMap(response => {
                return this.fetchInterestedMetrics(this.currentWorkspace.workspaceId)
              })).subscribe(response => {
              console.log("fetched interested metrics");
            }, error => {
              this.loggerService.error("fetching interested metrics");
            });

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
    } else if (this.description === null || this.description.trim() === "") {
      this.createError = "Enter some description";
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

  fetchWorkspacesAfterEditing(): any {
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

    }, error => {
      this.loggerService.error("Unable to fetch workspace after editing");
    });
  }

  submitWorkspace(): any {
    let payload = {};
    payload["email"] = this.selectedUser.email;
    payload["name"] = this.workspaceName;
    payload["description"] = this.description;
    payload["subscribe_to_alerts"] = this.subscribeToAlerts;
    payload["alert_emails"] = this.alertEmails;
    return this.apiService.post("/api/v1/performance/workspaces", payload).pipe(switchMap(response => {
      console.log("created/edited workspace successfully");
      return of(true);
    }));
  }

  onChangeSubscribeToAlerts(subscribed, workspace): void {
    workspace.subscribeToAlerts = subscribed;
    workspace.editingAlerts = true;
  }

  saveSubscribeAndEmailsForAlerts(workspace): void {
    this.workspaceName = workspace.name;
    this.description = workspace.description;
    this.subscribeToAlerts = workspace.subscribeToAlerts;
    this.alertEmails = workspace.alertEmails;
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.submitWorkspace();
      })).subscribe(response => {
      this.fetchWorkspacesAfterEditing();
      this.loggerService.success("saved the alerts for workspace");
    }, error => {
      this.loggerService.error("Unable to save alerts for workspace");
    });
  }

  deleteMetricInWorkspace(metricId): void {
    this.apiService.delete("/api/v1/performance/workspaces/" + this.currentWorkspace.workspaceId + "/interested_metrics?metric_id=" + metricId).subscribe(response => {
      this.loggerService.success(`deleted ${metricId}`);
      new Observable(observer => {
        observer.next(true);
        observer.complete();
        return () => {
        }
      }).pipe(
        switchMap(response => {
          return this.fetchInterestedMetrics(this.currentWorkspace.workspaceId)
        })).subscribe(response => {
        console.log("fetched interested metrics");
      }, error => {
        this.loggerService.error("fetching interested metrics");
      });
    });
  }

  onDeleteWorkspace(workspace) {
    this.apiService.delete("/api/v1/performance/workspaces?email=" + this.selectedUser.email + "&workspace_name=" + workspace.name).subscribe(response => {
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
      this.fetchWorkspacesAfterEditing();
    } else {
      workspace.editingWorkspace = false;
    }
  }

  openWorkspace(workspace): void {
    this.currentWorkspace = workspace;
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.fetchInterestedMetrics(workspace.workspaceId);
      })).pipe(
      switchMap(response => {
        let url = "/performance/workspace/" + this.selectedUser.email + "/" + this.currentWorkspace.name;
        this.router.navigateByUrl(url);
        return of(true);
      })).subscribe(response => {
      console.log("opened workspace");
    }, error => {
      this.loggerService.error("Unable to open workspace");
    });
  }

  getString(dict): string {
    return JSON.stringify(dict);
  }

  editWorkspace(workspace): void {
    this.currentWorkspace = workspace;
    workspace.editingWorkspace = true;
  }


  onChangeSubscribeTo(subscribed, metricId): void {
    for (let metric of this.currentWorkspace.interestedMetrics) {
      if (Number(metric.metric_id) == Number(metricId)) {
        metric.subscribe = subscribed;
      }
    }
  }

  onChangeTrack(tracking, metricId): void {
    for (let metric of this.currentWorkspace.interestedMetrics) {
      if (Number(metric.metric_id) == Number(metricId)) {
        metric.track = tracking;
      }
    }
  }

  saveInterestedMetrics(): any {
    let payload = {};
    payload["email"] = this.selectedUser.email;
    payload["workspace_id"] = this.currentWorkspace.workspaceId;
    payload["interested_metrics"] = this.currentWorkspace.interestedMetrics;
    return this.apiService.post("/api/v1/performance/workspaces/" + this.currentWorkspace.workspaceId + "/interested_metrics", payload).pipe(switchMap(response => {
      console.log("Edited interested metrics for the current workspace successfully");
      return of(true);
    }));
  }

  saveWorkspace(): void {
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        this.workspaceName = this.currentWorkspace.name;
        this.description = this.currentWorkspace.description;
        return this.submitWorkspace();
      }),
      switchMap(response => {
        return this.saveInterestedMetrics();
      })).subscribe(response => {
      this.fetchWorkspacesAfterEditing();
      this.loggerService.success("saved the workspace");
      this.modalService.dismissAll();
    }, error => {
      this.loggerService.error("Unable to save interested metrics");
    });
  }

}
