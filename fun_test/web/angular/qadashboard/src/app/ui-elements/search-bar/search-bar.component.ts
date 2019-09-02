import {Component, Input, OnInit, Output, EventEmitter} from '@angular/core';
import {Subject} from "rxjs";
import {debounceTime, distinctUntilChanged} from "rxjs/operators";

@Component({
  selector: 'app-search-bar',
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.css']
})
export class SearchBarComponent implements OnInit {
  @Input() placeHolder: string = null;
  @Output() textChanged: EventEmitter<string> = new EventEmitter<string>();
  searchText: string = null;
  searchTextUpdate = new Subject<string>();
  constructor() {
    this.searchTextUpdate.pipe(
      debounceTime(400),
      distinctUntilChanged())
      .subscribe(value => {
        //console.log(value);
        this.textChanged.emit(value);
      });

  }

  ngOnInit() {
  }

}
