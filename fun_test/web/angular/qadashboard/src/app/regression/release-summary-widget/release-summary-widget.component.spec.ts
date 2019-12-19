import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReleaseSummaryWidgetComponent } from './release-summary-widget.component';

describe('ReleaseSummaryWidgetComponent', () => {
  let component: ReleaseSummaryWidgetComponent;
  let fixture: ComponentFixture<ReleaseSummaryWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReleaseSummaryWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReleaseSummaryWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
