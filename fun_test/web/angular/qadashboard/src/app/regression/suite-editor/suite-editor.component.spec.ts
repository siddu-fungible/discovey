import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SuiteEditorComponent } from './suite-editor.component';

describe('SuiteEditorComponent', () => {
  let component: SuiteEditorComponent;
  let fixture: ComponentFixture<SuiteEditorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SuiteEditorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SuiteEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
