export class ReleaseCatalogSuite {
  id: number;
  constructor(id: number) {
    this.id = id;
  }
}



export class ReleaseCatalog {
  name: string = "Please update";
  suites: ReleaseCatalogSuite [] = [];
}
