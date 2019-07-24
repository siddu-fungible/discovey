import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SmokeTestStorageWidgetComponent } from './smoke-test-storage-widget.component';

describe('SmokeTestStorageWidgetComponent', () => {
  let component: SmokeTestStorageWidgetComponent;
  let fixture: ComponentFixture<SmokeTestStorageWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SmokeTestStorageWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SmokeTestStorageWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
