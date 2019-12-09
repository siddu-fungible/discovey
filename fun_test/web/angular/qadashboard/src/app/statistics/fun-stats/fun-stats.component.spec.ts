import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FunStatsComponent } from './fun-stats.component';

describe('FunStatsComponent', () => {
  let component: FunStatsComponent;
  let fixture: ComponentFixture<FunStatsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FunStatsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunStatsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
