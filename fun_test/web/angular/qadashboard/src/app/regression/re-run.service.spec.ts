import { TestBed, inject } from '@angular/core/testing';

import { ReRunService } from './re-run.service';

describe('ReRunService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ReRunService]
    });
  });

  it('should be created', inject([ReRunService], (service: ReRunService) => {
    expect(service).toBeTruthy();
  }));
});
