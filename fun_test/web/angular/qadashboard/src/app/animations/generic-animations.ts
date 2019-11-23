import {animate, state, style, transition, trigger} from "@angular/animations";

export const showAnimation = trigger('show', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(1200)
      ]),
      transition(':leave', [
        animate(1, style({ opacity: 1.0 }))
      ]),
      state('*', style({ opacity: 1.0 })),
    ]);
