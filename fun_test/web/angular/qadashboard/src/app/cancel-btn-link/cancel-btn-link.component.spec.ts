import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CancelBtnLinkComponent } from './cancel-btn-link.component';

describe('CancelBtnLinkComponent', () => {
  let component: CancelBtnLinkComponent;
  let fixture: ComponentFixture<CancelBtnLinkComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CancelBtnLinkComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CancelBtnLinkComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
