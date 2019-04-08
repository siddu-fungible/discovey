import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DpusComponent } from './dpus.component';

describe('DpusComponent', () => {
  let component: DpusComponent;
  let fixture: ComponentFixture<DpusComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DpusComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DpusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
