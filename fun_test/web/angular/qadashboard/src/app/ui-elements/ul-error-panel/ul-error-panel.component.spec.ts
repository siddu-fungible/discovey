import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { UlErrorPanelComponent } from './ul-error-panel.component';

describe('UlErrorPanelComponent', () => {
  let component: UlErrorPanelComponent;
  let fixture: ComponentFixture<UlErrorPanelComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ UlErrorPanelComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UlErrorPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
