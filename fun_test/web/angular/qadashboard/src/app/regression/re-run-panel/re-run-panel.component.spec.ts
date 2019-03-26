import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReRunPanelComponent } from './re-run-panel.component';

describe('ReRunPanelComponent', () => {
  let component: ReRunPanelComponent;
  let fixture: ComponentFixture<ReRunPanelComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReRunPanelComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReRunPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
