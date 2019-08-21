import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformanceViewWorkspaceComponent } from './performance-view-workspace.component';

describe('PerformanceViewWorkspaceComponent', () => {
  let component: PerformanceViewWorkspaceComponent;
  let fixture: ComponentFixture<PerformanceViewWorkspaceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerformanceViewWorkspaceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerformanceViewWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
