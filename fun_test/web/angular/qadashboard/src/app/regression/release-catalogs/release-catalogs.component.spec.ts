import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReleaseCatalogsComponent } from './release-catalogs.component';

describe('ReleaseCatalogsComponent', () => {
  let component: ReleaseCatalogsComponent;
  let fixture: ComponentFixture<ReleaseCatalogsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReleaseCatalogsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReleaseCatalogsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
