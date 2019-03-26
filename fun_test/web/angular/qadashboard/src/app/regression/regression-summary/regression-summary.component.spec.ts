import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RegressionSummaryComponent } from './regression-summary.component';

describe('RegressionSummaryComponent', () => {
  let component: RegressionSummaryComponent;
  let fixture: ComponentFixture<RegressionSummaryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RegressionSummaryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RegressionSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
