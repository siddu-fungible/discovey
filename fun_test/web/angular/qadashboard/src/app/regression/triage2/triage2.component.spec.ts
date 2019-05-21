import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Triage2Component } from './triage2.component';

describe('Triage2Component', () => {
  let component: Triage2Component;
  let fixture: ComponentFixture<Triage2Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Triage2Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Triage2Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
