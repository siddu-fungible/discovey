import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SmartLabelComponent } from './smart-label.component';

describe('SmartLabelComponent', () => {
  let component: SmartLabelComponent;
  let fixture: ComponentFixture<SmartLabelComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SmartLabelComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SmartLabelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
