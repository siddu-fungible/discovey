import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
} from '@angular/core';
import {LoggerService} from "../services/logger/logger.service";
import {ApiService} from "../services/api/api.service";
import {CommonService} from "../services/common/common.service";


@Component({
  selector: 'fun-card',
  templateUrl: './fun-card.component.html',
  styleUrls: ['./fun-card.component.css'],
})
export class FunCardComponent implements OnInit {

  @Input() title: any;
  @Input() subtitle: string;
  @Input() textTitle: string;
  @Input() iconLink: string;
  @Input() tooltipText: string;
  @Input() text: string;
  @Input() hideText: string;
  @Input() footerTextTitle: string;
  @Input() footerText: string;
  @Input() footerIconLink: string;
  @Input() footerTooltipText: string;
  @Input() enableFooter: boolean = false;
  @Input() icon: string;
  @Input() footerIcon: string;
  @Input() imageURL: string;


  constructor() {
  }

  ngOnInit() {
    console.log(this.title);
    console.log(this.subtitle);

  }

}
