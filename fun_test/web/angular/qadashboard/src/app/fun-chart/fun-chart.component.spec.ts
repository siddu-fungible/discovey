import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FunChartComponent } from './fun-chart.component';

describe('FunChartComponent', () => {
  let component: FunChartComponent;
  let fixture: ComponentFixture<FunChartComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FunChartComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
