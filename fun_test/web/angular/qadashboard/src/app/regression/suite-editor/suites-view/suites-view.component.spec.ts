import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SuitesViewComponent } from './suites-view.component';

describe('SuitesViewComponent', () => {
  let component: SuitesViewComponent;
  let fixture: ComponentFixture<SuitesViewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SuitesViewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SuitesViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});