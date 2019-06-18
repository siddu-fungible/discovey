import { TestBed, inject } from '@angular/core/testing';

import { TestBedService } from './test-bed.service';

describe('TestBedService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TestBedService]
    });
  });

  it('should be created', inject([TestBedService], (service: TestBedService) => {
    expect(service).toBeTruthy();
  }));
});
