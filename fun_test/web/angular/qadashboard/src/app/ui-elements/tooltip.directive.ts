import { Directive, Input, ElementRef, HostListener, Renderer2 } from '@angular/core';
import {CommonService} from 'src/app/services/common/common.service';

@Directive({
  selector: '[tooltip]'
})
export class TooltipDirective {
  @Input() placement: string;
  @Input() hideDelay: number = 1;
  @Input() tooltipContentString: any;
  @Input() tooltipContentCallback: Function = null;
  @Input() tooltipContentCallbackArg = null;
  tooltip: HTMLElement;
  offset = 0;

  constructor(private el: ElementRef, private renderer: Renderer2, private commonService: CommonService) { }

  @HostListener('mouseenter') onMouseEnter() {
    if (!this.tooltip) { this.show(); }
  }

  @HostListener('mouseleave') onMouseLeave() {
    if (this.tooltip) {
      this.hide();
    }
  }

  @HostListener("window:scroll", []) onWindowScroll() {
    if (this.tooltip) {
      this.hide();
    }
  }

  show() {
    this.create();
    this.setPosition();
    this.renderer.addClass(this.tooltip, 'fun-tooltip-show');
  }

  hide() {
    this.renderer.removeClass(this.tooltip, 'fun-tooltip-show');
    window.setTimeout(() => {
      this.renderer.removeChild(document.body, this.tooltip);
      this.tooltip = null;
    }, this.hideDelay);
  }

  create() {
    this.tooltip = this.renderer.createElement('span');

    if (this.tooltipContentString) {
      this.renderer.appendChild(
        this.tooltip,
        this.renderer.createText(this.tooltipContentString)
      );
    } else if (this.tooltipContentCallback) {
      if (!this.tooltipContentCallbackArg) {
        this.renderer.appendChild(this.tooltip, this.tooltipContentCallback())
      } else {
        this.renderer.appendChild(this.tooltip, this.tooltipContentCallback(this.el, this.tooltipContentCallbackArg));
      }

    }


    //this.renderer.
    //this.renderer.appendChild(document.body, this.toolTipContent);
    this.renderer.appendChild(this.el.nativeElement, this.tooltip);

    this.renderer.addClass(this.tooltip, 'fun-tooltip');
    this.renderer.addClass(this.tooltip, `fun-tooltip-${this.placement}`);
    //this.renderer.setStyle(this.tooltip, 'line-height', 1.6);
    //this.renderer.setStyle(this.tooltip, 'position', 'fixed');
    //this.renderer.setStyle(this.tooltip, 'font-size', '14px');
    //this.renderer.setStyle(this.tooltip, 'font-weight', '1');
    this.renderer.setStyle(this.tooltip, 'background-color', 'white');
    this.renderer.setStyle(this.tooltip, 'box-shadow', '0 4px 8px 0 rgba(0, 0, 0, 0.2)');
    this.renderer.setStyle(this.tooltip, 'border-radius', '10px');
    this.renderer.setStyle(this.tooltip, 'border', 'solid lightgrey 1px');

    /*this.renderer.setStyle(this.tooltip, '-webkit-transition', `opacity ${this.delay}ms`);
    this.renderer.setStyle(this.tooltip, '-moz-transition', `opacity ${this.delay}ms`);
    this.renderer.setStyle(this.tooltip, '-o-transition', `opacity ${this.delay}ms`);
    this.renderer.setStyle(this.tooltip, 'transition', `opacity ${this.delay}ms`);*/
  }



  setPosition() {
    const hostPos = this.el.nativeElement.getBoundingClientRect();

    const tooltipPos = this.tooltip.getBoundingClientRect();

    const scrollPos = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;

    let top, left;
    if (this.placement === 'top') {
      top = hostPos.top - tooltipPos.height - this.offset;
      left = hostPos.left + (hostPos.width - tooltipPos.width)/2;
    }

    if (this.placement === 'bottom') {
      top = hostPos.bottom + this.offset;
      left = hostPos.left + (hostPos.width - tooltipPos.width) / 2;
    }

    if (this.placement === 'left') {
      top = hostPos.top + (hostPos.height - tooltipPos.height) / 2;
      left = hostPos.left - tooltipPos.width - this.offset;
    }

    if (this.placement === 'right') {
      top = hostPos.top + (hostPos.height - tooltipPos.height) / 2;
      left = hostPos.right + 10;
    }

    this.renderer.setStyle(this.tooltip, 'top', `${top}px`);
    this.renderer.setStyle(this.tooltip, 'left', `${left}px`);
  }
}
