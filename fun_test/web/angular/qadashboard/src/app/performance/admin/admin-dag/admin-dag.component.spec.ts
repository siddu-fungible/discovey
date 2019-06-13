import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminDagComponent } from './admin-dag.component';

describe('AdminDagComponent', () => {
  let component: AdminDagComponent;
  let fixture: ComponentFixture<AdminDagComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AdminDagComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AdminDagComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
