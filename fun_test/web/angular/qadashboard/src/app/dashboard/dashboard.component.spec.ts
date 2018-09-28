import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardComponent } from './dashboard.component';
import { PerformanceComponent } from "../performance/performance.component";
import {FunTableComponent} from "../fun-table/fun-table.component";
import {HttpClient, HttpHandler} from "@angular/common/http";
import {MatSortModule} from '@angular/material';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { TestComponent } from "../test/test.component";
import {LoggerService} from "../services/logger/logger.service";

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DashboardComponent, PerformanceComponent, TestComponent, FunTableComponent],
      imports: [MatSortModule, BrowserAnimationsModule],
      providers: [HttpClient, HttpHandler, LoggerService]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
