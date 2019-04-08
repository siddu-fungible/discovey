import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScriptHistoryComponent } from './script-history.component';

describe('ScriptHistoryComponent', () => {
  let component: ScriptHistoryComponent;
  let fixture: ComponentFixture<ScriptHistoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScriptHistoryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScriptHistoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
