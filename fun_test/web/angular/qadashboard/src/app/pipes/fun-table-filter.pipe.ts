import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'funTableFilter',
  pure: true
})
export class FunTableFilterPipe implements PipeTransform {

  transform(items: any[], filter: Map<number, boolean>): any {
    console.log("Filter Pipe");
    if (!items || !filter) {
            return items;
        }

        return items.filter(item => {
            if(items.indexOf(item) < filter.size && filter.get(items.indexOf(item))) {
              return true;
            }
            return false;
        });
  }

}
