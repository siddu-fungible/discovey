import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformanceSummaryWidgetComponent } from './performance-summary-widget.component';

describe('PerformanceSummaryWidgetComponent', () => {
  let component: PerformanceSummaryWidgetComponent;
  let fixture: ComponentFixture<PerformanceSummaryWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerformanceSummaryWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerformanceSummaryWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
