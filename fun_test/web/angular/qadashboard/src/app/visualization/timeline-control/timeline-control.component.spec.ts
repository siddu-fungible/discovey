import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TimelineControlComponent } from './timeline-control.component';

describe('TimelineControlComponent', () => {
  let component: TimelineControlComponent;
  let fixture: ComponentFixture<TimelineControlComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TimelineControlComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TimelineControlComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
