import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GitHistoryComponent } from './git-history.component';

describe('GitHistoryComponent', () => {
  let component: GitHistoryComponent;
  let fixture: ComponentFixture<GitHistoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GitHistoryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GitHistoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
