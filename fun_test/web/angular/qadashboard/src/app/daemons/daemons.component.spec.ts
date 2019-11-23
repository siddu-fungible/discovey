import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DaemonsComponent } from './daemons.component';

describe('DaemonsComponent', () => {
  let component: DaemonsComponent;
  let fixture: ComponentFixture<DaemonsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DaemonsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DaemonsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
