import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NetworkFuncpSanityWidgetComponent } from './network-funcp-sanity-widget.component';

describe('NetworkFuncpSanityWidgetComponent', () => {
  let component: NetworkFuncpSanityWidgetComponent;
  let fixture: ComponentFixture<NetworkFuncpSanityWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NetworkFuncpSanityWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NetworkFuncpSanityWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
