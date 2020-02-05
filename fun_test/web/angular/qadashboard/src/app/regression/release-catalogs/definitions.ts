import {Api} from "../../lib/api";
import {Suite} from "../suite-editor/suite-editor.service";
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";

export class ReleaseSuiteExecutionHistoryElement {
  job_id: number;
  job_result: string;

  constructor(props) {
    Object.assign(this, props);
  }

  serialize() {
    return {"job_id": this.job_id, "job_result": this.job_result};
  }
}

export class ReleaseSuiteExecution extends Api {
  classType = ReleaseSuiteExecution;
  suite_id: number;
  test_bed_name: string = null;
  suite_details: Suite;
  selected: boolean = false;
  job_id: number = null;
  error_message: string = null;
  job_status: number = null;
  job_result: string = null;
  re_run_request: boolean = false;
  re_run_request_submitted: boolean = false;
  showingScripts: boolean = false;
  modifyingTestBed: boolean = false;
  showingRunHistory: boolean = false;
  run_history: ReleaseSuiteExecutionHistoryElement [] = [];

  constructor(props) {
    super();
    Object.keys(props).forEach(key => {
      if (key === "suite_id") {
        this.suite_id = props.suite_id;
      }
      if (key === "test_bed_name") {
        this.test_bed_name = props.test_bed_name;
      }
      if (key === "job_id") {
        this.job_id = props.job_id;
      }
      if (key === "error_message") {
        this.error_message = props.error_message;
      }
      if (key === "suite_details") {
        this.suite_details = props.suite_details;
      }
      if (key === "re_run_request_submitted") {
        this.re_run_request_submitted = props.re_run_request_submitted;
      }
      if (key === "run_history") {
        this.run_history = props.run_history.map(historyElement => new ReleaseSuiteExecutionHistoryElement(historyElement));
      }


    })
  }


  serialize() {
    return {suite_id: this.suite_id,
      test_bed_name: this.test_bed_name,
      job_id: this.job_id,
      re_run_request: this.re_run_request
    };
  }
}

export class ReleaseCatalogExecution extends Api {
  classType = ReleaseCatalogExecution;
  url = "/api/v1/regression/release_catalog_executions";
  id: number;
  created_date_timestamp: number;
  started_date_timestamp: number;
  completion_date_timestamp: number;
  owner: string = null;
  state: number;
  result: string = null;
  release_catalog_id: number;
  description: string = "TBD";
  recurring: boolean = true;
  release_train: string = "master";
  ready_for_execution: boolean = false;
  master_execution_id: number = null;
  suite_executions: ReleaseSuiteExecution [] = [];
  deleted: boolean = false;
  error_message: string = null;
  build_number: number = null;
  update_last_good_build: boolean = false;

  customDeserializableProperties = ["suite_executions"];
  deserializationHooks = {suite_executions: function(data)  {
      return data.map(dataElement => {
        return new ReleaseSuiteExecution(dataElement);
      })
    }
  };

  serialize() {
    return {
      owner: this.owner,
      state: this.state,
      release_catalog_id: this.release_catalog_id,
      description: this.description,
      recurring: this.recurring,
      release_train: this.release_train,
      suite_executions: this.suite_executions.map(suiteElement => suiteElement.serialize()),
      ready_for_execution: this.ready_for_execution,
      update_last_good_build: this.update_last_good_build
    }
  }

  public getUrl(params) {
    let url = this.url;
    if (params.hasOwnProperty('id')) {
      url = `${url}/${params.id}`;
    }
    return url;
  }


}
