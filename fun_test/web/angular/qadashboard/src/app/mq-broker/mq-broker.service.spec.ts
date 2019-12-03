import { TestBed, inject } from '@angular/core/testing';

import { MqBrokerService } from './mq-broker.service';

describe('MqBrokerService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [MqBrokerService]
    });
  });

  it('should be created', inject([MqBrokerService], (service: MqBrokerService) => {
    expect(service).toBeTruthy();
  }));
});
