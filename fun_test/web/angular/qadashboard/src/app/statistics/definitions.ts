import {timestamp} from "rxjs/operators";

export class FunTimeSeries {
  name: string = null;
  data: {[timestamp: number]: any} = {};
  // data: any[] = [];
  constructor(name: string, data: {[timestamp: number]: any}) {
    this.name = name;
    this.data = data;
  }
  toJson() {
    return {name: this.name,
    data: this.data};
  }
}

export class FunTimeSeriesCollection {
  name: string = null;
  unit: string = null;
  collection: FunTimeSeries[] = [];
  constructor(name: string, unit: string, collection: FunTimeSeries[]) {
    this.name = name;
    this.unit = unit;
    this.collection = collection;
  }
  toJson() {
    return {name: this.name,
    unit: this.unit,
    collection: this.collection};
  }
}

