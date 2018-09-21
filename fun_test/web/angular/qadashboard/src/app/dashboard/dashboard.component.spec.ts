import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardComponent } from './dashboard.component';
import { PerformanceComponent } from "../performance/performance.component";
import { TestComponent } from "../test/test.component";
import {HttpClient, HttpHandler} from "@angular/common/http";
import {LoggerService} from "../services/logger/logger.service";

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DashboardComponent, PerformanceComponent, TestComponent],
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
