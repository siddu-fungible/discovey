import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformanceAttachDagComponent } from './performance-attach-dag.component';

describe('PerformanceAttachDagComponent', () => {
  let component: PerformanceAttachDagComponent;
  let fixture: ComponentFixture<PerformanceAttachDagComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerformanceAttachDagComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerformanceAttachDagComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
