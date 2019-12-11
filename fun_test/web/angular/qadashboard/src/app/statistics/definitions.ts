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
  // title: string = null;
  name: string = null;
  unit: string = null;
  collection: FunTimeSeries[] = [];
  // xValues: any[] = [];
  // y1Values: FunTimeSeries[] = [];
  // y2AxisLabel: string = null;
  // y2Values: string = null;
  constructor(name: string, unit: string, collection: FunTimeSeries[]) {
    // this.title = title;
    // this.xAxisLabel = xAxisLabel;
    // this.y1AxisLabel = y1AxisLabel;
    // this.y1Values = y1Values;
    // this.xValues = xValues;
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

