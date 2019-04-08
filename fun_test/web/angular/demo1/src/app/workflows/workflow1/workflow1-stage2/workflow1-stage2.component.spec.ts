import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Workflow1Stage2Component } from './workflow1-stage2.component';

describe('Workflow1Stage2Component', () => {
  let component: Workflow1Stage2Component;
  let fixture: ComponentFixture<Workflow1Stage2Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Workflow1Stage2Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Workflow1Stage2Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
