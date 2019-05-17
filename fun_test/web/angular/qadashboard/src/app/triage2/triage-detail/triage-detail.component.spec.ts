import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TriageDetailComponent } from './triage-detail.component';

describe('TriageDetailComponent', () => {
  let component: TriageDetailComponent;
  let fixture: ComponentFixture<TriageDetailComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TriageDetailComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TriageDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
