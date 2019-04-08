import { Directive } from '@angular/core';
import { AfterViewInit } from "@angular/core";
import { ElementRef } from "@angular/core";

@Directive({
  selector: '[scrollTo]'
})
export class ScrollToDirective implements AfterViewInit {

  constructor(private elRef:ElementRef) { }
  ngAfterViewInit() { this.elRef.nativeElement.scrollIntoView(); }

}
