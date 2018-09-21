import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FunTableComponent } from './fun-table.component';
import {MatSortModule} from '@angular/material';

describe('FunTableComponent', () => {
  let component: FunTableComponent;
  let fixture: ComponentFixture<FunTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FunTableComponent ],
      imports: [MatSortModule],
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FunTableComponent);
    component = fixture.componentInstance;
    // fixture.detectChanges();
  });

  afterEach(() => {
    fixture.detectChanges();
  });

  it('should create', () => {
    component.data = new Array(1);
    component.data = {"rows": [],"headers": []};
    // component.data["rows"] = [];
    // component.data["headers"] = [];
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });
  // it('testing without headers and data', async(() => {
  //   component.data["rows"] = [];
  //   component.data["headers"] = [];
  // }));
  // it('testing with both headers and data', async(() => {
  //    component.data["rows"] = [['hi','hello']];
  //   component.data["headers"] = ['names', 'numbers'];
  // }));
  // it('testing without data', async(() => {
  //    component.data["rows"] = [];
  //   component.data["headers"] = ['names', 'numbers'];
  // }));
  // it('testing without headers', async(() => {
  //    component.data["rows"] = [['hi','hello']];
  //   component.data["headers"] = [];
  // }));
});
