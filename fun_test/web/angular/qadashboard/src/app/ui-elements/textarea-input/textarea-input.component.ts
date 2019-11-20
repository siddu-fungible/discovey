import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';

@Component({
  selector: 'app-textarea-input',
  templateUrl: './textarea-input.component.html',
  styleUrls: ['./textarea-input.component.css']
})
export class TextareaInputComponent implements OnInit {
  @Input() initialValue: string = null;
  @Input() numRows: number = 1; // number of rows of the text-area
  @Input() hoverHide: boolean = true; // The pencil shows only if you hover
  @Input() editable: boolean = true;
  tempValue: string = null;
  editing: boolean = false;
  @Output() valueChanged = new EventEmitter<string>();


  constructor() { }

  ngOnInit() {
    this.tempValue = this.initialValue;
  }

  onEdit() {
    this.editing = true;
  }

  onSubmit() {
    this.editing = false;
    this.valueChanged.emit(this.tempValue);
    this.initialValue = this.tempValue;
  }

  onCancel() {
    this.tempValue = this.initialValue;
    this.editing = false;
  }

}
