import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FunSpinnerComponent } from './fun-spinner.component';

describe('FunSpinnerComponent', () => {
  let component: FunSpinnerComponent;
  let fixture: ComponentFixture<FunSpinnerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FunSpinnerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunSpinnerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
