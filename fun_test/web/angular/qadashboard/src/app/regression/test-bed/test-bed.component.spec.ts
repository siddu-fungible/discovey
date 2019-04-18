import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TestBedComponent } from './test-bed.component';

describe('TestBedComponent', () => {
  let component: TestBedComponent;
  let fixture: ComponentFixture<TestBedComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TestBedComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TestBedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
