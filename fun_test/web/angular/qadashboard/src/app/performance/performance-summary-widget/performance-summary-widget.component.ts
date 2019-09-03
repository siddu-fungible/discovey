import {Component, OnInit, Input, OnChanges, Output, EventEmitter, Renderer2} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";
import {from, Observable, of} from "rxjs";
import {mergeMap, switchMap} from "rxjs/operators";
import {CommonService} from "../../services/common/common.service";

@Component({
  selector: 'app-performance-summary-widget',
  templateUrl: './performance-summary-widget.component.html',
  styleUrls: ['./performance-summary-widget.component.css']
})
export class PerformanceSummaryWidgetComponent implements OnInit {

  clickUrls: any = {};


  y1Values: any = [];
  x1Values: any = [];
  isDone: boolean = false;

  constructor(private apiService: ApiService, private logger: LoggerService,
              private renderer: Renderer2, private commonService: CommonService) {
  }

  initializeY1Values() {
    this.y1Values = [{
      name: 'Good',
      data: [],
      color: 'green'
    },
      {
        name: 'Bad',
        data: [],
        color: 'red'
      }
    ];
  }


  ngOnInit() {

    this.initializeY1Values();

    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(switchMap(response => {
      return this.fetchDag();
    })).subscribe(response => {
    }, error => {
      this.logger.error('Failed to fetch dag');
    });
  }


  fetchDag() {
    return this.apiService.get("/metrics/dag" + "?levels=1" + "&starting_metrics=101").pipe(switchMap((response) => {
      let dag = response.data[0].children_info;
      for (let i in dag) {
        this.x1Values.push(dag[i].chart_name);
        this.clickUrls[dag[i].chart_name] = '/performance?goto=F1%2F' + dag[i].chart_name;
        let recentScore = dag[i].last_two_scores[0];
        recentScore = +recentScore.toFixed(2);
        if (recentScore <= 50) {
          this.y1Values[0].data.push(0);
          this.y1Values[1].data.push(recentScore);
        } else {
          this.y1Values[0].data.push(recentScore);
          this.y1Values[1].data.push(0);
        }
      }
      this.isDone = true;
      return of(true);
    }));
  }
}

