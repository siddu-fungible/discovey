import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformanceWorkspaceComponent } from './performance-workspace.component';

describe('WorkspaceComponent', () => {
  let component: PerformanceWorkspaceComponent;
  let fixture: ComponentFixture<PerformanceWorkspaceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerformanceWorkspaceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerformanceWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
