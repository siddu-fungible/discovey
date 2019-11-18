export class ReleaseCatalogSuite {
  id: number;
}

export class ReleaseCatalog {
  description: string = "Please update";
  suites: ReleaseCatalogSuite [] = [];
}
