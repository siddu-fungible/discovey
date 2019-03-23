import { TestBed, inject } from '@angular/core/testing';

import { RegressionService } from './regression.service';

describe('RegressionService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [RegressionService]
    });
  });

  it('should be created', inject([RegressionService], (service: RegressionService) => {
    expect(service).toBeTruthy();
  }));
});
