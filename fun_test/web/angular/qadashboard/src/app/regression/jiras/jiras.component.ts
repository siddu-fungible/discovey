import { Component, OnInit } from '@angular/core';
import {switchMap} from "rxjs/operators";
import {of} from "rxjs";
import {RegressionService} from "../regression.service";

@Component({
  selector: 'app-jiras',
  templateUrl: './jiras.component.html',
  styleUrls: ['./jiras.component.css']
})
export class JirasComponent implements OnInit {
  jiraMap: any = null;
  constructor(private regressionService: RegressionService) { }

  ngOnInit() {
    this.getAllRegressionJiras().subscribe();
  }

  getAllRegressionJiras() {
    let scriptPk = null;

    return this.regressionService.getScriptInfo(null).pipe(switchMap(response => {
      let tempMap = {};
      response.map(item => {
        if (!tempMap.hasOwnProperty(item.bug)) {
          tempMap[item.bug] = {scripts: []};
        }
        tempMap[item.bug].scripts.push({pk: item.pk, scriptPath: item.script_path});
      });

      for (let key in tempMap) {
        this.setContext(tempMap[key]);
      }
      this.jiraMap = tempMap;
      return of(true);
    }));
  }
  setContext(item) {
    let i = 0;

    let s = "";

    item.scripts.map(scriptItem => {
      let pk = scriptItem.pk;
      let scriptPath = scriptItem.scriptPath;
      s += `<a target="_blank" href='/regression/summary?script_pk=${pk}'>` + scriptPath + "</a>"
      s += "<br>";
    });
    item["context"] = s;

  }


}
