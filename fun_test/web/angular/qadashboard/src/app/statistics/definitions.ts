export class FunTimeSeries {
  name: string = null;
  data: any[] = [];
  constructor(name: string, data: any[]) {
    this.name = name;
    this.data = data;
  }
  toJson() {
    return {name: this.name,
    data: this.data};
  }
}

export class FunTimeSeriesCollection {
  title: string = null;
  xAxisLabel: string = null;
  y1AxisLabel: string  = null;
  xValues: any[] = [];
  y1Values: FunTimeSeries[] = [];
  y2AxisLabel: string = null;
  y2Values: string = null;
  constructor(title: string, xAxisLabel: string, y1AxisLabel: string, xValues: any[], y1Values: FunTimeSeries[]) {
    this.title = title;
    this.xAxisLabel = xAxisLabel;
    this.y1AxisLabel = y1AxisLabel;
    this.y1Values = y1Values;
    this.xValues = xValues;
  }
  toJson() {
    return {title: this.title,
    xAxisLabel: this.xAxisLabel,
    y1AxisLable: this.y1AxisLabel,
    y1Values: this.y1Values,
    xValues: this.xValues};
  }
}

