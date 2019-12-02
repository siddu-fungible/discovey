import { Injectable } from '@angular/core';

export class StatisticsCategory {
  name: string;
  display_name: string;
}

export class StatisticsSubCategory {
  name: string;
  display_name: string;
}

@Injectable({
  providedIn: 'root'
})
export class StatisticsService {

  constructor() { }
}
