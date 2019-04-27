import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JirasComponent } from './jiras.component';

describe('JirasComponent', () => {
  let component: JirasComponent;
  let fixture: ComponentFixture<JirasComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ JirasComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JirasComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
