import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DpuComponent } from './dpu.component';

describe('DpuComponent', () => {
  let component: DpuComponent;
  let fixture: ComponentFixture<DpuComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DpuComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DpuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
