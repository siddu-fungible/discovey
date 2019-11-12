import { TestBed, inject } from '@angular/core/testing';

import { ScriptDetailService } from './script-detail.service';

describe('ScriptDetailService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ScriptDetailService]
    });
  });

  it('should be created', inject([ScriptDetailService], (service: ScriptDetailService) => {
    expect(service).toBeTruthy();
  }));
});
