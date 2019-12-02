import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BrokerTestComponent } from './broker-test.component';

describe('BrokerTestComponent', () => {
  let component: BrokerTestComponent;
  let fixture: ComponentFixture<BrokerTestComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BrokerTestComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BrokerTestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
