import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScoresTableComponent } from './scores-table.component';

describe('ScoresTableComponent', () => {
  let component: ScoresTableComponent;
  let fixture: ComponentFixture<ScoresTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScoresTableComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScoresTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
