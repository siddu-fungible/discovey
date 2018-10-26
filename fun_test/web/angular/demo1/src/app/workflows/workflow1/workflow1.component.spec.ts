import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Workflow1Component } from './workflow1.component';

describe('Workflow1Component', () => {
  let component: Workflow1Component;
  let fixture: ComponentFixture<Workflow1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Workflow1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Workflow1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
