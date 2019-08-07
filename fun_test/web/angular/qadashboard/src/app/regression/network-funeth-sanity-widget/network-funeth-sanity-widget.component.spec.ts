import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NetworkFunethSanityWidgetComponent } from './network-funeth-sanity-widget.component';

describe('NetworkFunethSanityWidgetComponent', () => {
  let component: NetworkFunethSanityWidgetComponent;
  let fixture: ComponentFixture<NetworkFunethSanityWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NetworkFunethSanityWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NetworkFunethSanityWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
