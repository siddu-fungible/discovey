import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformanceShowChartsWorkspaceComponent } from './performance-show-charts-workspace.component';

describe('PerformanceShowChartsWorkspaceComponent', () => {
  let component: PerformanceShowChartsWorkspaceComponent;
  let fixture: ComponentFixture<PerformanceShowChartsWorkspaceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerformanceShowChartsWorkspaceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerformanceShowChartsWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
