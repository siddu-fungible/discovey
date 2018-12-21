import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SuiteDetailComponent } from './suite-detail.component';

describe('SuiteDetailComponent', () => {
  let component: SuiteDetailComponent;
  let fixture: ComponentFixture<SuiteDetailComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SuiteDetailComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SuiteDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
