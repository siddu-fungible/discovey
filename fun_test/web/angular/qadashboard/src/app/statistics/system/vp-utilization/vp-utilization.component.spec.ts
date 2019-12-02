import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VpUtilizationComponent } from './vp-utilization.component';

describe('VpUtilizationComponent', () => {
  let component: VpUtilizationComponent;
  let fixture: ComponentFixture<VpUtilizationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VpUtilizationComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VpUtilizationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
