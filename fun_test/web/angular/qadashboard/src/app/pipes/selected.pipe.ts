import { Pipe, PipeTransform } from '@angular/core';
import {ContextInfo} from "../regression/script-detail/script-detail.service";

@Pipe({
  name: 'selected',
  pure: false

})
export class SelectedPipe implements PipeTransform {

  transform(values: any [], args?: any): any {
    return values.filter(element => element.selected);

  }

}
