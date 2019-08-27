import { TestBed, inject } from '@angular/core/testing';

import { SuiteEditorService } from './suite-editor.service';

describe('SuiteEditorService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [SuiteEditorService]
    });
  });

  it('should be created', inject([SuiteEditorService], (service: SuiteEditorService) => {
    expect(service).toBeTruthy();
  }));
});
