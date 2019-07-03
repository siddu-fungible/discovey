import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RegressionSummaryWidgetComponent } from './regression-summary-widget.component';

describe('RegressionSummaryWidgetComponent', () => {
  let component: RegressionSummaryWidgetComponent;
  let fixture: ComponentFixture<RegressionSummaryWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RegressionSummaryWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RegressionSummaryWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
