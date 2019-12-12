import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FunStatsTableComponent } from './fun-stats-table.component';

describe('FunStatsTableComponent', () => {
  let component: FunStatsTableComponent;
  let fixture: ComponentFixture<FunStatsTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FunStatsTableComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunStatsTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
