import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {ButtonType, FunButtonWithIcon} from "../definitions";

@Component({
  selector: 'app-section-header',
  templateUrl: './section-header.component.html',
  styleUrls: ['./section-header.component.css']
})
export class SectionHeaderComponent implements OnInit {
  @Input() title: string;
  @Input() staticTitle: string = null;
  @Input() subText1: string = null;
  @Input() subText2: string = null;
  @Input() editable: boolean = false;
  @Input() subSection: boolean = false;
  @Input() leftAlignedButtons: FunButtonWithIcon [];
  @Output() editingCallback = new EventEmitter<string>();
  editing: boolean = false;
  hoverHide: boolean = true;
  tempValue: string = null;
  constructor() { }

  ngOnInit() {
    this.tempValue = this.title;
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

}
