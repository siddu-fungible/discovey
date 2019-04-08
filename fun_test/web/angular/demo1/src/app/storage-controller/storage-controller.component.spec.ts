import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { StorageControllerComponent } from './storage-controller.component';

describe('StorageControllerComponent', () => {
  let component: StorageControllerComponent;
  let fixture: ComponentFixture<StorageControllerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ StorageControllerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StorageControllerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
