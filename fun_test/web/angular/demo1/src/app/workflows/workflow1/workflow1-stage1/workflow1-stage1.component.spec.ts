import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Workflow1Stage1Component } from './workflow1-stage1.component';

describe('Workflow1Stage1Component', () => {
  let component: Workflow1Stage1Component;
  let fixture: ComponentFixture<Workflow1Stage1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Workflow1Stage1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Workflow1Stage1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
