import {Api} from "../../lib/api";
import {Suite} from "../suite-editor/suite-editor.service";

export class ReleaseSuiteExecution {
  suite_id: number;
  test_bed_name: string;
  suite_details: Suite;

  constructor(props) {
    this.suite_id = props.suite_id;
    if (props.hasOwnProperty('test_bed_name')) {
      this.test_bed_name = props
    }
    this.suite_details = props.suite_details;
  }
  serialize() {
    return {suite_id: this.suite_id, test_bed_name: this.test_bed_name};
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
  master_execution_id: number = null;
  suiteExecutions: ReleaseSuiteExecution [] = [];

  /*
  deSerialize(data: any) {

    if (data.hasOwnProperty('id')) {
      this.id = data.id;
    }
    if (data.hasOwnProperty('created_date_timestamp')) {
      this.created_date_timestamp = data.created_date_timestamp;
    }
    if (data.hasOwnProperty('started_date_timestamp')) {
      this.started_date_timestamp = data.started_date_timestamp;
    }
    if (data.hasOwnProperty('completion_date_timestamp')) {
      this.completion_date_timestamp = data.completion_date_timestamp;
    }
    if (data.hasOwnProperty('owner')) {
      this.owner = data.owner;
    }
    if (data.hasOwnProperty('state')) {
      this.state = data.state;
    }
    if (data.hasOwnProperty('release_catalog_id')) {
      this.release_catalog_id = data.release_catalog_id;
    }
    if (data.hasOwnProperty('description')) {
      this.description = data.description;
    }
    if (data.hasOwnProperty('recurring')) {
      this.recurring = data.recurring;
    }
  }*/

  serialize() {
    return {
      owner: this.owner,
      state: this.state,
      release_catalog_id: this.release_catalog_id,
      description: this.description,
      recurring: this.recurring,
      release_train: this.release_train,
      suite_executions: this.suiteExecutions.map(suiteElement => suiteElement.serialize())
    }
  }

}
