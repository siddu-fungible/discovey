import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SuiteExecutionWidgetComponent } from './suite-execution-widget.component';

describe('SuiteExecutionWidgetComponent', () => {
  let component: SuiteExecutionWidgetComponent;
  let fixture: ComponentFixture<SuiteExecutionWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SuiteExecutionWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SuiteExecutionWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
