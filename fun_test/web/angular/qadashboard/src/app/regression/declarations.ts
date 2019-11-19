export class ReleaseCatalogSuite {
  id: number;
  constructor(id: number) {
    this.id = id;
  }
}



export class ReleaseCatalog {
  description: string = "Please update";
  suites: ReleaseCatalogSuite [] = [];
}
