export class ReleaseCatalogSuite {
  id: number;
  constructor(id: number) {
    this.id = id;
  }
  toJson() {
    return {id: this.id};
  }
}

export class ReleaseCatalog {
  name: string = "Please update";
  description: string = "Please update";
  suites: ReleaseCatalogSuite [] = [];
  id: number;
  constructor (fields?: {
      name?: string
      suites?: ReleaseCatalogSuite[]
    }) {
    if (fields) {
      Object.keys(fields).forEach(field => {
        if (field === "name") {
          this.name = fields["name"];
        } else if (field === "description") {
          this.description = fields["description"];
        } else if (field === "suites") {
          this.suites = fields["suites"].map(suite => new ReleaseCatalogSuite(suite.id));
        } else {
          this[field] = fields[field];
        }
      });
    }
  }

  payloadForUpdate() {
    let payload = {};
    payload["name"] = this.name;
    payload["description"] = this.description;
    payload["suites"] = this.suites.map(suite => suite.toJson());
    return payload;
  }
}
