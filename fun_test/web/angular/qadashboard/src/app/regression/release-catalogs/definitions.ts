import {Api} from "../../lib/api";
import {Suite} from "../suite-editor/suite-editor.service";

export class ReleaseSuiteExecution extends Api {
  classType = ReleaseSuiteExecution;
  suite_id: number;
  test_bed_name: string;
  suite_details: Suite;
  selected: boolean = false;
  job_id: number = null;
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
    })
  }
  serialize() {
    return {suite_id: this.suite_id, test_bed_name: this.test_bed_name, job_id: this.job_id};
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
  release_catalog_id: number;
  description: string = "TBD";
  recurring: boolean = true;
  release_train: string = "master";
  ready_for_execution: boolean = false;
  master_execution_id: number = null;
  suite_executions: ReleaseSuiteExecution [] = [];
  deleted: boolean = false;

  showingScripts: boolean = false;
  modifyingTestBed: boolean = false;
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
      ready_for_execution: this.ready_for_execution
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
