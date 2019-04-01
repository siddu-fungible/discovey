import {Component, Input, OnInit, ViewChild, TemplateRef} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {ActivatedRoute} from "@angular/router";
import {CommonService} from "../services/common/common.service";
import {NgbModal, ModalDismissReasons} from '@ng-bootstrap/ng-bootstrap';
import {Location, LocationStrategy, PathLocationStrategy} from '@angular/common';

@Component({
  selector: 'git-history',
  templateUrl: './triage.component.html',
  styleUrls: ['./triage.component.css'],
  providers: [Location, {provide: LocationStrategy, useClass: PathLocationStrategy}]
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
  showCommits: boolean = false;
  startButton: boolean = true;
  faultyAuthor: string = null;
  successAuthor: string = null;
  triageFlows: any = null;
  triageDetails: any = null;
  fault: string = null;
  triageStatus: string = "Active";
  closeResult: string;
  continueTriaging: boolean = true;
  maxTries: string = null;
  timePercentage: any = null;

  showForm: boolean = false;
  selectedOption: string = null;
  triagingOptions: any = [];
  triageId: number;

  fromDate: any;
  toDate: any;
  bootArgs: string = null;
  funOSMakeFlags: string = null;
  email: string = null;
  fromCommit: string = null;
  toCommit: string = null;
  advancedInfo: boolean = false;
  location: Location;
  emulationUrl = "https://github.com/fungible-inc/FunDevelopment/tree/master/emulation_schedule";
  validated: boolean = false;

  @ViewChild("content") modalContent: TemplateRef<any>;

  constructor(private apiService: ApiService, private logger: LoggerService, private route: ActivatedRoute,
              private commonService: CommonService, private modalService: NgbModal, private loc: Location) {
    this.location = loc;
  }

  ngOnInit() {
    this.status = "Fetching Commits";
    // this.triagingOptions.push("SCORES");
    this.triagingOptions.push("PASS/FAIL");
    this.fromDate = null;
    this.toDate = null;
    this.bootArgs = null;
    this.funOSMakeFlags = null;
    this.email = null;
    this.selectedOption = null;
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.id = params['id'];
        this.triageId = this.id;
        this.checkTriageDb();
      } else if (this.id) {
        this.triageId = this.id;
        this.checkTriageDb();
      } else {
        this.showForm = true;
        this.status = null;
      }
    });


  }

  kill(triageId): void {
    let payload = {};
    payload["triage_id"] = triageId;
    this.apiService.post('/triage/kill_db', payload).subscribe(response => {
      if (response.data) {
        alert("Killed triaging");
      } else {
        alert("Unable to kill triage");
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
      "commits": this.commits,
      "triage_info": this.triageInfo
    };
    this.apiService.post('/triage/insert_db', payload).subscribe(response => {
      this.showForm = false;
      this.triageId = response.data;
      this.showTriaging();
      this.location.prepareExternalUrl("triaging/" + String(this.triageId));
      this.location.go("triaging/" + String(this.triageId));
      alert("submitted");
    }, error => {
      this.logger.error("Updating DB Failed");
    });
  }

  showTriaging(): void {
    this.showCommits = false;
    this.showChanged = false;
    this.showForm = false;
    this.status = "Fetching Status";
    this.refreshStatus();
  }

  checkStatus(): void {
    let statusFlag = false;
    for (let flow of this.triageFlows) {
      if (flow.status === "Active") {
        statusFlag = true;
      }
    }
    if (!statusFlag) {
      this.fault = this.faultyCommit;
      this.triageStatus = "Not found";
      this.continueTriaging = false;
    }
  }

  stopTriaging(): void {
    this.continueTriaging = false;
    if (!this.continueTriaging) {
      let git_commit = "";
      let statusFlag = false;
      let detail = this.triageDetails;
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
    if (this.commits) {
      for (let commit of this.commits) {
        if (commit.hexsha === fault) {
          this.showFilesChanged(commit);
        }
      }
    } else {
      this.status = "Fetching changed files";
      this.fetchGitCommits();
    }
  }

  refreshStatus(): void {
    let payload = {"triage_id": this.triageId};
    this.apiService.post('/triage/fetch_flows', payload).subscribe((data) => {
      let result = data.data;
      this.triageFlows = result.flows;
      this.triageDetails = result.triage[0];
      let detail = this.triageDetails;
      this.triageStatus = detail.status;
      this.fault = detail.faulty_commit;
      if (detail.status !== "Active") {
        this.continueTriaging = false;
      }
      let totalTries = 0;
      let tries = 0;
      for (let flow of this.triageFlows) {
        if (flow.status === "Completed" || flow.status === "Failed") {
          tries += 1;
        }
        if (flow.status !== "Suspended") {
          totalTries += 1;
        }
        if (!this.continueTriaging && flow.status === "Failed") {
          this.fault = flow.git_commit;
        }
        // if (flow.score !== -1 && flow.score < detail.last_good_score) {
        //   git_commit = flow.git_commit;
        // }
      }
      this.maxTries = String(tries) + "/" + String(totalTries);
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
    if (this.commits) {
      this.showChanged = false;
      this.showTriagingStatus = false;
      this.showCommits = true;
    } else {
      this.status = "Fetching commits";
      this.showChanged = false;
      this.showTriagingStatus = false;
      this.showCommits = true;
      this.fetchGitCommits();
    }
  }

  openGitUrl(sha): void {
    let url = "https://github.com/fungible-inc/FunOS/commit/" + sha;
    window.open(url, '_blank');
  }

  openJenkinsUrl(jenkinsId): void {
    let url = "http://jenkins-sw-master:8080/job/emulation/job/fun_on_demand/" + jenkinsId;
    window.open(url, '_blank');
  }

  openLsfUrl(lsfId): void {
    let url = "http://palladium-jobs.fungible.local:8080/job/" + lsfId;
    window.open(url, '_blank');
  }

  getPercentage(): string {
    return this.timePercentage;
  }

  setCommits(): void {
    let payload = {
      "metric_id": this.id,
      "metric_type": this.selectedOption,
      "from_date": this.fromDate,
      "to_date": this.toDate,
      "boot_args": this.bootArgs,
      "fun_os_make_flags": this.funOSMakeFlags,
      "email": this.email
    };
    this.apiService.post('/metrics/get_triage_info', payload).subscribe((data) => {
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
      this.logger.error("Traiging info fetch failed");
    });
    // let payload = {"metric_id": this.id};
    // this.apiService.post('/metrics/first_degrade', payload).subscribe((data) goBack=> {
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
    //   this.logger.error("Past Status Urls");
    // });

  }

  validateFields(): void {
    if (this.fromCommit && this.toCommit && this.bootArgs && this.email && this.selectedOption) {
      this.validated = true;
    } else {
      this.validated = false;
      alert("Please fill all the required fields");
    }
  }

  getInfoFromCommits(): void {
    this.validateFields();
    if (this.validated) {
      this.status = "Triaging commits";
      let payload = {
        "metric_type": this.selectedOption,
        "from_commit": this.fromCommit,
        "to_commit": this.toCommit,
        "boot_args": this.bootArgs,
        "fun_os_make_flags": this.funOSMakeFlags,
        "email": this.email
      };
      this.apiService.post('/metrics/get_triage_info_from_commits', payload).subscribe((data) => {
        let result = data.data;
        this.triageInfo = result;
        this.successCommit = this.toCommit;
        this.faultyCommit = this.fromCommit;
        this.fetchGitCommits();
      }, error => {
        this.logger.error("Traiging info fetch failed");
      });
    }
  }

  checkTriageDb(): void {
    let payload = {"triage_id": this.id};
    this.apiService.post('/triage/check_db', payload).subscribe(response => {
      let result = response.data;
      if (result["metric_type"]) {
        this.selectedOption = result["metric_type"];
        this.bootArgs = result["boot_args"];
        this.funOSMakeFlags = result["fun_os_make_flags"];
        this.email = result["email"];
        this.faultyCommit = result["from_commit"];
        this.successCommit = result["to_commit"];
        this.showForm = false;
        this.startButton = false;
        this.showTriaging();
      } else {
        this.showForm = true;
        this.status = null;
      }
      // this.setCommits();
      // this.getInfoFromCommits();
    }, error => {
      this.logger.error("checking DB Failed");
    });
  }

  openParams(): void {
    window.open(this.emulationUrl, '_blank');
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
        if (this.showTriagingStatus) {
          this.showCommits = false;
          this.openFaultyCommitDetails(this.fault);
        } else {
          this.showCommits = true;
        }
        this.status = null;
      }, error => {
        this.logger.error("Fetching git Commits between the faulty and success commits");
      });
    } else {
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
    let klass = "danger";
    if (result === "Failed") {
      klass = "danger";
    } else if (result === "Completed") {
      klass = "success";
    } else if (result === "Active") {
      klass = "warning";
    } else if (result === "Success") {
      klass = "success";
    } else if (result === "Building on Jenkins") {
      klass = "info";
    } else if (result === "Jenkins build complete") {
      klass = "info";
    } else if (result === "Running on Lsf") {
      klass = "info";
    } else if (result === "Waiting") {
      klass = "muted";
    } else if (result === "Suspended") {
      klass = "default";
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

  reRun(commit): void {

  }

  moreTriaging(): void {
    this.continueTriaging = true;
  }
}
