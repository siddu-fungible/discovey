import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformanceShowReportWorkspaceComponent } from './performance-show-report-workspace.component';

describe('PerformanceShowReportWorkspaceComponent', () => {
  let component: PerformanceShowReportWorkspaceComponent;
  let fixture: ComponentFixture<PerformanceShowReportWorkspaceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerformanceShowReportWorkspaceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerformanceShowReportWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
