import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformanceComponent } from './performance.component';
import {HttpClient, HttpHandler} from "@angular/common/http";
import {Observable, of, throwError} from "rxjs";
import {catchError, map} from "rxjs/operators";
import {ApiResponse, ApiService} from "../services/api/api.service";

export class MockApiService {
    post(url: string, payload: any): Observable<ApiResponse> {
      let o = new ApiResponse();
    return of(o);
  }
}

describe('PerformanceComponent', () => {
  let component: PerformanceComponent;
  let fixture: ComponentFixture<PerformanceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerformanceComponent ],
      providers: [HttpClient, HttpHandler]

    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerformanceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    jasmine.getEnv().allowRespy(true);
    let service = fixture.debugElement.injector.get(ApiService);
    component = fixture.componentInstance;
    expect(component).toBeTruthy();


    spyOn(service, 'post').and.returnValue(of(new ApiResponse({message: "Mock1"})));
    component.doSomething1();
    expect(component.getComponentState()).toMatch("Mock1");

    spyOn(service, 'post').and.returnValue(throwError(new ApiResponse({message: "Mock2"})));
    component.doSomething1();
    expect(component.getComponentState()).toMatch("Error");


  });
});
