import {animate, state, style, transition, trigger} from "@angular/animations";

export const showAnimation = trigger('show', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500)
      ]),
      transition(':leave', [
        animate(500, style({ opacity: 0 }))
      ]),
      state('*', style({ opacity: 1.0 })),
    ]);


export const slideInOutAnimation = trigger('slideInOut', [

      transition(':enter', [
        style({transform: 'translateX(-100%)'}),
        animate('500ms ease-in-out', style({transform: 'translateX(0%)'}))
      ]),
      transition(':leave', [
        animate('500ms ease-in-out', style({transform: 'translateX(-100%)'}))
      ])
    ]);
