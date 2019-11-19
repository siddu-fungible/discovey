export class ReleaseCatalogSuite {
  id: number;
  constructor(id: number) {
    this.id = id;
  }
}

export class ReleaseCatalog {
  name: string = "Please update";
  description: string = null;
  suites: ReleaseCatalogSuite [] = [];
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

        } else {
          this[field] = fields[field];
        }
      });
    }
  }
}
