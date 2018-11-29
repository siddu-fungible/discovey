import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class CommonService {

  constructor() { }

  scrollTo(elementId) {
    let element = document.getElementById(elementId);
    window.scrollTo({left: 0, top: element.offsetTop, behavior: "smooth"});
  }
}
