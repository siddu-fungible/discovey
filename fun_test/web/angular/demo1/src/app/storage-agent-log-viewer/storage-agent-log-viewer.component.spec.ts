import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { StorageAgentLogViewerComponent } from './storage-agent-log-viewer.component';

describe('StorageAgentLogViewerComponent', () => {
  let component: StorageAgentLogViewerComponent;
  let fixture: ComponentFixture<StorageAgentLogViewerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ StorageAgentLogViewerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StorageAgentLogViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
