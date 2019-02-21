import {Component, Input, OnInit, ViewChild, TemplateRef} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {CommonService} from "../services/common/common.service";
import {NgbModal, ModalDismissReasons} from '@ng-bootstrap/ng-bootstrap';
import {DataSharingService} from "../services/data-sharing/data-sharing.service";
import {Subscription} from "rxjs";

@Component({
  selector: 'git-history',
  templateUrl: './triage.component.html',
  styleUrls: ['./triage.component.css']
})
export class TriageComponent implements OnInit {
  @Input() id: number = null;
  // @Input() faultyCommit: string = null;
  // @Input() successCommit: string = '0af7f75c8a6f89620792ecd6f46212cda81a40b3';
  faultyCommit: string = null;
  successCommit: string = null;
  commits: any = null;
  changedFiles: any = null;
  commitDates: any = null;
  status: string = null;
  showChanged: boolean = false;
  gitCommit: any = null;
  faultyMessage: string = null;
  successMessage: string = null;
  totalShow: boolean = false;
  gitUser: string = null;
  triageInfo: any = null;
  showTriagingStatus: boolean = false;
  showCommits: boolean = true;
  startButton: boolean = true;
  faultyAuthor: string = null;
  successAuthor: string = null;
  triageFlows: any = null;
  triageDetails: any = null;
  fault: string = null;
  triageStatus: string = "ACTIVE";
  closeResult: string;
  continueTriaging: boolean = true;
  maxTries: string = null;
  timePercentage: any = null;
  message: any = null;
  subscription: Subscription;

  @ViewChild("content") modalContent: TemplateRef<any>;

  constructor(private apiService: ApiService, private logger: LoggerService, private route: ActivatedRoute,
              private commonService: CommonService, private modalService: NgbModal, private sharedData: DataSharingService) {
  }

  ngOnInit() {
    this.status = "Fetching Commits";
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.id = params['id'];
        this.checkTriageDb();
      }
      else if (this.id) {
        this.checkTriageDb()
      }
    });


  }

  showModal(git_commit) {
    this.modalService.open(this.modalContent, {ariaLabelledBy: 'modal-title'}).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
      if (result === "OK click") {
        this.continueTriaging = true;
        this.checkStatus();
      } else {
        this.continueTriaging = false;
        this.updateStatus(git_commit);
      }
    }, (reason) => {
      this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
      if (reason === "Cross click") {
        this.continueTriaging = true;
      }
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

  updateStatus(git_commit): void {
    let payload = {
      "metric_id": this.id,
      "faulty_commit": git_commit
    };
    this.apiService.post('/triage/update_db', payload).subscribe(response => {
      this.fault = response.data.faulty_commit;
      this.triageStatus = response.data.status;
    }, error => {
      this.logger.error("Updating DB Failed");
    });
  }

  startTriaging(): void {
    let payload = {
      "metric_id": this.id,
      "commits": this.commits,
      "triage_info": this.triageInfo
    };
    this.apiService.post('/triage/insert_db', payload).subscribe(response => {
      this.startButton = false;
      this.showTriaging();
      alert("submitted");
    }, error => {
      this.logger.error("Updating DB Failed");
    });
  }

  showTriaging(): void {
    this.showCommits = false;
    this.showChanged = false;
    this.status = "Fetching Status";
    this.refreshStatus();
  }

  checkStatus(): void {
    let statusFlag = false;
    for (let flow of this.triageFlows) {
      if (flow.status === "ACTIVE") {
        statusFlag = true;
      }
    }
    if (!statusFlag) {
      this.fault = this.faultyCommit;
      this.triageStatus = "NOT FOUND";
      this.continueTriaging = false;
    }
  }

  stopTriaging(): void {
    this.continueTriaging = false;
    if (!this.continueTriaging) {
      let git_commit = "";
      let statusFlag = false;
      let detail = this.triageDetails[0];
      for (let flow of this.triageFlows) {
        if (flow.score !== -1 && flow.score < detail.last_good_score) {
          git_commit = flow.git_commit;
        }
      }
      if (git_commit !== "") {
        this.updateStatus(git_commit);
      } else {
        this.updateStatus(this.faultyCommit);
      }

    }
  }

  openFaultyCommitDetails(fault): void {
    for (let commit of this.commits) {
      if (commit.hexsha === fault) {
        this.showFilesChanged(commit);
      }
    }
  }

  refreshStatus(): void {
    let payload = {"metric_id": this.id};
    this.apiService.post('/triage/fetch_flows', payload).subscribe((data) => {
      let result = data.data;
      this.triageFlows = result.flows;
      this.triageDetails = result.triage;
      let detail = this.triageDetails[0];
      this.triageStatus = detail.status;
      this.fault = detail.faulty_commit;
      if (detail.status !== "ACTIVE") {
        this.continueTriaging = false;
      }
      let git_commit = "";
      let tries = 0;
      for (let flow of this.triageFlows) {
        if (flow.status === "COMPLETED" || flow.status === "FAILED") {
          tries += 1;
        }
        // if (flow.score !== -1 && flow.score < detail.last_good_score) {
        //   git_commit = flow.git_commit;
        // }
      }
      this.maxTries = String(tries) + "/" + String(detail.max_tries);
      let currentDate = new Date();
      let diff = currentDate.getTime() - new Date(detail.date_time).getTime();
      let time_elapsed = diff / 60000;
      this.timePercentage = Math.round(time_elapsed) + " min / 90 min (Max)";
      // if (this.modalContent && this.continueTriaging && git_commit !== "") {
      //   this.showModal(git_commit);
      // }
      this.showTriagingStatus = true;
      this.status = null;
    }, error => {
      this.logger.error("Fetching Status Failed");
    });
  }

  goBack(): void {
    this.showChanged = false;
    this.showTriagingStatus = false;
    this.showCommits = true;
  }

  getPercentage(): string {
    return this.timePercentage;
  }

  setCommits(): void {
    // this.subscription = this.sharedData.getMessage().subscribe(message => {
    //   this.message = message;
    // let payload = {"metric_id": this.id,
    // "metric_type": this.message["metric_type"],
    // "from_date": this.message["from_date"],
    // "to_date": this.message["to_date"],
    // "boot_args": this.message["boot_args"]};
    // this.apiService.post('/metrics/get_triage_info', payload).subscribe((data) => {
    //   let result = data.data;
    //   this.triageInfo = result;
    //   if (result.passed_git_commit && result.passed_git_commit !== "") {
    //     this.successCommit = result.passed_git_commit;
    //   }
    //   if (result.degraded_git_commit && result.degraded_git_commit !== "") {
    //     this.faultyCommit = result.degraded_git_commit;
    //   }
    //   this.fetchGitCommits();
    // }, error => {
    //   this.logger.error("Traiging info fetch failed");
    // })
    // });
    let payload = {"metric_id": this.id};
    this.apiService.post('/metrics/first_degrade', payload).subscribe((data) => {
      let result = data.data;
      this.triageInfo = result;
      if (result.passed_git_commit && result.passed_git_commit !== "") {
        this.successCommit = result.passed_git_commit;
      }
      if (result.degraded_git_commit && result.degraded_git_commit !== "") {
        this.faultyCommit = result.degraded_git_commit;
      }
      this.fetchGitCommits();
    }, error => {
      this.logger.error("Past Status Urls");
    });

  }

  checkTriageDb(): void {
    let payload = {"metric_id": this.id};
    this.apiService.post('/triage/check_db', payload).subscribe(response => {
      if (response.data) {
        this.startButton = false;
        this.showTriaging();
      }
      // this.setCommits();
    }, error => {
      this.logger.error("checking DB Failed");
    });
  }

  fetchGitCommits(): void {
    if (this.faultyCommit && this.successCommit) {
      let payload = {};
      payload = {
        "faulty_commit": this.faultyCommit,
        "success_commit": this.successCommit
      };
      this.apiService.post('/metrics/git_commits', payload).subscribe(result => {
        this.commits = result.data.commits;
        let total = this.commits.length - 1;
        this.faultyMessage = this.commits[0].message;
        this.faultyAuthor = this.commits[0].author;
        this.successAuthor = this.commits[total].author;
        this.successMessage = this.commits[total].message;
        this.status = null;
      }, error => {
        this.logger.error("Fetching git Commits between the faulty and success commits");
      });
    }
    else {
      this.status = null;
      console.log("Git commit is missing from the data");
    }
  }

  showFilesChanged(commit): void {
    this.showChanged = true;
    this.totalShow = false;
    this.commonService.scrollTo("changed-files");
    this.changedFiles = commit.changed_files;
    this.gitCommit = commit.hexsha;
    this.gitUser = commit.author;

  }

  showTotalFilesCHanged(): void {
    this.showChanged = true;
    this.totalShow = true;
    this.commonService.scrollTo("changed-files");
    let changedFiles = new Set();
    for (let commit of this.commits) {
      for (let file of commit.changed_files) {
        changedFiles.add(file);
      }
    }
    this.changedFiles = changedFiles;
  }

  resultToClass(result): string {
    result = result.toUpperCase();
    let klass = "default";
    if (result === "FAILED") {
      klass = "danger";
    } else if (result === "COMPLETED") {
      klass = "success";
    } else if (result === "ACTIVE") {
      klass = "warning";
    } else if (result === "SUCCESS") {
      klass = "success";
    }
    return klass;
  }

  testEntry(): void {
    let payload = {"metric_id": this.id};
    this.apiService.post('/triage/test', payload).subscribe((data) => {
      let result = data.data;
    }, error => {
      this.logger.error("Testing entry Failed");
    });
  }

  moreTriaging(): void {
    this.continueTriaging = true;
  }
}
