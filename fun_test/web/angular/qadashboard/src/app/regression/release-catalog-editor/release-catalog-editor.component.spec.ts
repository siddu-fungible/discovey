import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReleaseCatalogEditorComponent } from './release-catalog-editor.component';

describe('ReleaseCatalogEditorComponent', () => {
  let component: ReleaseCatalogEditorComponent;
  let fixture: ComponentFixture<ReleaseCatalogEditorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReleaseCatalogEditorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReleaseCatalogEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
