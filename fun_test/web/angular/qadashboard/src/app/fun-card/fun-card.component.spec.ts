import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FunCardComponent } from './fun-card.component';

describe('FunCardComponent', () => {
  let component: FunCardComponent;
  let fixture: ComponentFixture<FunCardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FunCardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
