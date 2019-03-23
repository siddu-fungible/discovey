import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RegressionSummaryChartComponent } from './regression-summary-chart.component';

describe('RegressionSummaryChartComponent', () => {
  let component: RegressionSummaryChartComponent;
  let fixture: ComponentFixture<RegressionSummaryChartComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RegressionSummaryChartComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RegressionSummaryChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
