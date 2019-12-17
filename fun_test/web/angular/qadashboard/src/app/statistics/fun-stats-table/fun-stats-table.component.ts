import {Component, Input, OnInit} from '@angular/core';
import {CommonService} from "../../services/common/common.service";

@Component({
  selector: 'fun-stats-table',
  templateUrl: './fun-stats-table.component.html',
  styleUrls: ['./fun-stats-table.component.css']
})
export class FunStatsTableComponent implements OnInit {
  @Input() tableHeaders: any = null;
  @Input() tableData: any = null;

  filteredTableData: any[] = [];
  characterLimit: number = 25;

  constructor(private commonService: CommonService) { }

  ngOnInit() {
    this.filteredTableData = [];
    for (let record of this.tableData) {
      let oneRecord = [];
      for (let value of record) {
        let oneValue = {};
        let newValue = value;
        oneValue["stringType"] = true;
        if (typeof value !== 'string') {
          newValue = JSON.stringify(value);
          oneValue["stringType"] = false;
        }
        oneValue["originalStringValue"] = newValue;
        if (newValue.length > this.characterLimit) {
          oneValue["originalValue"] = value;
          oneValue["slicedValue"] = newValue.slice(0, this.characterLimit);
          oneValue["showSliced"] = true;
        } else {
          oneValue["originalValue"] = value;
          oneValue["slicedValue"] = newValue;
          oneValue["showSliced"] = false;
        }
        oneRecord.push(oneValue);
      }
      this.filteredTableData.push(oneRecord);
    }
  }

   expandSlicedString(d): void {
    d.showSliced = !d.showSliced;
  }

  isString(value): boolean {
    return typeof value === 'string';
  }

}
