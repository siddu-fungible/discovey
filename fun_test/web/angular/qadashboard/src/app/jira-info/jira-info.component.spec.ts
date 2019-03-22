import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JiraInfoComponent } from './jira-info.component';

describe('JiraInfoComponent', () => {
  let component: JiraInfoComponent;
  let fixture: ComponentFixture<JiraInfoComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ JiraInfoComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JiraInfoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
