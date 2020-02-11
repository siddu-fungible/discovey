import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LastGoodBuildComponent } from './last-good-build.component';

describe('LastGoodBuildComponent', () => {
  let component: LastGoodBuildComponent;
  let fixture: ComponentFixture<LastGoodBuildComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LastGoodBuildComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LastGoodBuildComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
