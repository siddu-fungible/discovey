import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NetworkSanityWidgetComponent } from './network-sanity-widget.component';

describe('NetworkSanityWidgetComponent', () => {
  let component: NetworkSanityWidgetComponent;
  let fixture: ComponentFixture<NetworkSanityWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NetworkSanityWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NetworkSanityWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
