import {Component, OnInit, forwardRef, Output, EventEmitter, Input} from '@angular/core';
import {ControlValueAccessor, NG_VALUE_ACCESSOR, FormControl, Validator, NG_VALIDATORS} from "@angular/forms";

@Component({
  selector: 'app-json-input',
  templateUrl: './json-input.component.html',
  styleUrls: ['./json-input.component.css'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => JsonInputComponent),
      multi: true
    },
    {
      provide: NG_VALIDATORS,
      useExisting: forwardRef(() => JsonInputComponent),
      multi: true,
    }]
})
export class JsonInputComponent implements OnInit, ControlValueAccessor {
  @Input() ensureArrayOfNumbers: boolean = false;
  @Output() dataChanged = new EventEmitter<string>();
  @Input() numRows: number = 6; // number of rows for the text-area
  @Input() disabled: boolean = false;
  data: any = null;
  jsonString: string = null;
  parseError: boolean = false;
  notArrayOfNumbers: boolean = false;
  propagateChange: any = null;
  public result = {};

  constructor() {
  }

  ngOnInit() {
  }

  public registerOnTouched() {
  }

  public writeValue(obj: any) {
    if (obj) {
      this.data = obj;
      // this will format it with 4 character spacing
      this.jsonString = JSON.stringify(this.data, undefined, 4);
    }
  }

  public registerOnChange(fn: any) {
    this.propagateChange = fn;

  }

  public isArrayOfNumbers(value) {
    let result = false;
    if (Array.isArray(value) && (value.every(it => typeof it === 'number'))) {
      result = true;
    }
    return result;
  }

  public onChange(event) {

    // get value from text area
    let newValue = event.target.value;
    this.parseError = false;
    this.notArrayOfNumbers = false;
    try {
      // parse it to json
      if (newValue && newValue.length > 0) {
        this.data = JSON.parse(newValue);
        if (this.ensureArrayOfNumbers && !this.isArrayOfNumbers(this.data)) {
          this.notArrayOfNumbers = true;
          throw Error(`Not an array of numbers`);
        } else {
        }
        this.dataChanged.emit(this.data);
      }
    } catch (ex) {
      // set parse error if it fails
      this.data = null;
      this.parseError = true;
      this.dataChanged.emit(null);
    }

    // update the form
    if (this.propagateChange) {
      this.propagateChange(this.data);
    }
  }

  onJsonDataChanged(event) {

  }


}
