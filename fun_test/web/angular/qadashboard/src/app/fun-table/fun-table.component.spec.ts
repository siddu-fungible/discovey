import {async, ComponentFixture, TestBed} from '@angular/core/testing';

import {FunTableComponent} from './fun-table.component';
import {MatSortModule} from '@angular/material';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {LoggerService} from "../services/logger/logger.service";
import {HttpClient, HttpHandler} from "../../../node_modules/@angular/common/http";

describe('FunTableComponent', () => {
  let component: FunTableComponent;
  let fixture: ComponentFixture<FunTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [FunTableComponent],
      imports: [MatSortModule, BrowserAnimationsModule],
      providers: [LoggerService]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunTableComponent);
    component = fixture.componentInstance;
    // fixture.detectChanges();
  });

  afterEach(() => {
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
  it('testing without headers and data', async(() => {
    component.data = new Array(1);
    component.data = {"rows": [], "headers": []};
    fixture.detectChanges();
    expect(component).toBeTruthy();
  }));
  it('testing with both headers and data', async(() => {
    component.data = new Array(1);
    component.data = {"rows": ['hi', 'hello'], "headers": ['first', 'last']};
    fixture.detectChanges();
    expect(component).toBeTruthy();
  }));
  it('testing without data', async(() => {
    component.data = new Array(1);
    component.data = {"rows": [], "headers": ['first', 'last']};
    fixture.detectChanges();
    expect(component).toBeTruthy();
  }));
  it('testing without headers', async(() => {
    component.data = new Array(1);
    component.data = {"rows": ['hi', 'hello'], "headers": []};
    fixture.detectChanges();
    expect(component).toBeTruthy();
  }));

  it('populating with more rows and columns', async(() => {
    component.data = new Array(1);
    component.data = {"rows": [], "headers": [], "currentPageIndex": -1, "totalLength": 14, "pageSize": 10};
    for (let i = 1; i <= 10000; i++) {
      component.data.rows.push([i, i + 1]);
    }
    for (let j = 1; j <= 20; j++) {
      component.data.headers.push([j]);
    }
    fixture.detectChanges();
    // component.ngOnChanges();
    expect(component).toBeTruthy();
  }));

  it('Invalid Page number', async(() => {
    // component.data = new Array(1);
    component.data = {"rows": [['hi', 'hello']], "headers": ['first', 'last'], "currentPageIndex": -1};
    component.ngOnChanges();
    fixture.detectChanges();
    expect(component).toBeTruthy();
  }));


});
