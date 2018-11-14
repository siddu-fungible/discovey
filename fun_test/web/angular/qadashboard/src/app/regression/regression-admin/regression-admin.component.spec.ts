import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RegressionAdminComponent } from './regression-admin.component';

describe('RegressionAdminComponent', () => {
  let component: RegressionAdminComponent;
  let fixture: ComponentFixture<RegressionAdminComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RegressionAdminComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RegressionAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
