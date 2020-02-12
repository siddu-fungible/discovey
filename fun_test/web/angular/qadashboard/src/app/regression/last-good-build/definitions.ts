import {Api} from "../../lib/api";

export class LastGoodBuild extends Api {
  classType = LastGoodBuild;
  url = "/api/v1/regression/last_good_build";
  release_train: string = null;
  build_number: number;
  release_catalog_execution_id: number = -1;

  serialize() {
    return {
      release_train: this.release_train,
      build_number: this.build_number,
      release_catalog_execution_id: this.release_catalog_execution_id
    }
  }

  public getUrl(params) {
    let url = this.url;
    if (params.hasOwnProperty('release_train')) {
      url = `${url}/${params.release_train}`;
    }
    return url;
  }


}
