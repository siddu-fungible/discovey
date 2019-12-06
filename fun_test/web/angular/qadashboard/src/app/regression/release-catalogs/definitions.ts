import {Api} from "../../lib/api";

export class ReleaseCatalogExecution extends Api {
  classType = ReleaseCatalogExecution;
  url = "/api/v1/regression/release_catalog_executions";
  id: number;
  created_date_timestamp: number;
  started_date_timestamp: number;
  completion_date_timestamp: number;
  owner: string;
  state: number;
  release_catalog_id: number;

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
  }

  serialize() {
    return {
      owner: this.owner,
      state: this.state,
      release_catalog_id: this.release_catalog_id
    }
  }

}
