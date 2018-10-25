import {Component, OnInit, Input} from '@angular/core';
import {PagerService} from "../services/pager/pager.service";
import {ApiService} from "../services/api/api.service";
import {ActivatedRoute} from "@angular/router";
import {Title} from "@angular/platform-browser";

enum Filter {
    All = "ALL",
    Completed = "COMPLETED",
    Pending = "PENDING"
}

@Component({
  selector: 'app-regression',
  templateUrl: './regression.component.html',
  styleUrls: ['./regression.component.css']
})

export class RegressionComponent implements OnInit {
  pager: any = {};
  suiteExecutionsCount: number;
  recordsPerPage: number;
  @Input() tags: string;
  @Input() filterString: string = Filter.All;
  items: any;
  logDir: any;
  status: string = "Fetching Data";

  constructor(private pagerService: PagerService, private apiService: ApiService, private route: ActivatedRoute,
              private title: Title) {
  }

  ngOnInit() {
    this.title.setTitle('Regression');
    if (this.route.snapshot.data["tags"]) {
      this.tags = this.route.snapshot.data["tags"];
    }
    this.route.params.subscribe(params => {
      if (params['filterString']) {
        let urlString = params['filterString'];
        if (urlString === "completed_jobs") {
          this.filterString = Filter.Completed;
        } else if (urlString === "pending_jobs") {
          this.filterString = Filter.Pending;
        } else {
          this.filterString = Filter.All;
        }
      }
      if (params['tags']) {
        this.tags = '["' + params["tags"] + '"]';
      }
    });
    this.recordsPerPage = 20;
    this.logDir = null;
    this.suiteExecutionsCount = 0;
    let payload = {};
    if (this.tags) {
      payload["tags"] = this.tags;
    }
    let self = this;
    this.apiService.post("/regression/suite_executions_count1/" + this.filterString, payload).subscribe((result) => {
      this.suiteExecutionsCount = (parseInt(result.data));
      this.setPage(1);
    });
    if (!this.logDir) {
      this.apiService.get("/regression/log_path").subscribe(function (result) {
        self.logDir = result.data;
      }, error => {
        self.logDir = "/static/logs/s_";
      });
    }
    this.status = null;
  }

  setPage(page) {
    this.status = "Fetching Data";
    this.pager = this.pagerService.getPager(this.suiteExecutionsCount, page, this.recordsPerPage);
    if (page === 0 || (page > this.pager.endPage)) {
      return;
    }
    let payload = {};
    if (this.tags) {
      payload["tags"] = this.tags;
    }
    this.apiService.post("/regression/suite_executions1/" + this.recordsPerPage + "/" + page + "/" + this.filterString, payload).subscribe(result => {
      this.items = JSON.parse(result.data);
    });
    this.status = null;
  }

  testCaseLength = function (testCases) {
    return JSON.parse(testCases).length;
  };

  trimTime(t) {
    return t.replace(/\..*$/, "").replace(/T/, " ");
  }

  getSuiteDetail(suiteId) {
    console.log(suiteId);
    window.location.href = "/regression/suite_detail/" + suiteId;
  }

  getSchedulerLog(suiteId) {
    if (this.logDir) {
      return this.logDir + suiteId + "/scheduler.log.txt"; // TODO
    }
  }

  getSchedulerLogDir(suiteId) {
    if (this.logDir) {
      return "/regression/static_serve_log_directory/" + suiteId;
    }
  }

  rerunClick(suiteId) {
    this.apiService.get("/regression/suite_re_run/" + suiteId).subscribe(function (result) {
      let jobId = parseInt(result.data);
      window.location.href = "/regression/suite_detail/" + jobId;
    });
  }

  killClick(suiteId) {
    this.apiService.get("/regression/kill_job/" + suiteId).subscribe(function (result) {
      let jobId = parseInt(result.data);
      window.location.href = "/regression/";
    });
  }

  getTagList = function (tagsString) {
    return JSON.parse(tagsString);
  }

  resultToClass(result): any {
    result = result.toUpperCase();
    let klass = "default";
    if (result === "FAILED") {
      klass = "danger";
    } else if (result === "PASSED") {
      klass = "success";
    } else if (result === "SKIPPED") {
      klass = "warning";
    } else if (result === "NOT_RUN") {
      klass = "default";
    } else if (result === "IN_PROGRESS") {
      klass = "info";
    } else if (result === "BLOCKED") {
      klass = "blocked";
    }
    return klass;
  }

}
