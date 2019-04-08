import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SectionHorizontalLineComponent } from './section-horizontal-line.component';

describe('SectionHorizontalLineComponent', () => {
  let component: SectionHorizontalLineComponent;
  let fixture: ComponentFixture<SectionHorizontalLineComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SectionHorizontalLineComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SectionHorizontalLineComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
