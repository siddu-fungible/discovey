import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JobSpecComponent } from './job-spec.component';

describe('JobSpecComponent', () => {
  let component: JobSpecComponent;
  let fixture: ComponentFixture<JobSpecComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ JobSpecComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JobSpecComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
