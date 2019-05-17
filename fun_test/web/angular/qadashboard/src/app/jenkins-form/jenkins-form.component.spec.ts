import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JenkinsFormComponent } from './jenkins-form.component';

describe('JenkinsFormComponent', () => {
  let component: JenkinsFormComponent;
  let fixture: ComponentFixture<JenkinsFormComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ JenkinsFormComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JenkinsFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
