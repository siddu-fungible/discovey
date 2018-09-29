import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FunMetricChartComponent } from './fun-metric-chart.component';

describe('FunMetricChartComponent', () => {
  let component: FunMetricChartComponent;
  let fixture: ComponentFixture<FunMetricChartComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FunMetricChartComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunMetricChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
