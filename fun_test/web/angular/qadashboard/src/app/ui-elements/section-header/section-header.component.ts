import {Component, EventEmitter, Input, OnChanges, OnInit, Output} from '@angular/core';
import {ButtonType, FunActionLink, FunButtonWithIcon} from "../definitions";

@Component({
  selector: 'app-section-header',
  templateUrl: './section-header.component.html',
  styleUrls: ['./section-header.component.css']
})
export class SectionHeaderComponent implements OnInit, OnChanges {
  @Input() title: string;
  @Input() staticTitle: string = null;
  @Input() subText1: string = null;
  @Input() subText2: string = null;
  @Input() editable: boolean = false;
  @Input() subSection: boolean = false;
  @Input() leftAlignedButtons: FunButtonWithIcon [];
  @Input() titleLeftAlignedButtons: FunButtonWithIcon [];
  @Input() titleStateLabel: string = null;
  @Input() titleResultLabel: string = null;
  @Input() titleActionLinks: FunActionLink [];
  @Input() nextHeaderTitle: string = null;
  @Output() editingCallback = new EventEmitter<string>();
  editing: boolean = false;
  hoverHide: boolean = true;
  tempValue: string = null;
  constructor() { }

  ngOnInit() {
    this.tempValue = this.title;
  }

  ngOnChanges() {
    let i = 0;
    console.log(this.titleStateLabel);
  }

  onEditClick() {
    this.editing = !this.editing;
  }

  onSubmitClick() {
    this.editingCallback.emit(this.tempValue);
    this.editing = false;
  }

  onCancelClick() {
    this.editing = false;
  }

  onButtonClick(buttonObject) {
    buttonObject.callback();
  }

  onLinkClick(linkObject) {
    linkObject.callback(linkObject.data);
  }
}
