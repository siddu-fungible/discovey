import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SchedulerAdminComponent } from './scheduler-admin.component';

describe('SchedulerAdminComponent', () => {
  let component: SchedulerAdminComponent;
  let fixture: ComponentFixture<SchedulerAdminComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedulerAdminComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedulerAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
