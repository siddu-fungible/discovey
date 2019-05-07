import {Component, OnInit, forwardRef, Output, EventEmitter} from '@angular/core';
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
export class JsonInputComponent implements OnInit, ControlValueAccessor, Validator {
  @Output() dataChanged = new EventEmitter<string>();
  data: any = null;
  jsonString: string = null;
  parseError: boolean = false;
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

  public validate(c: FormControl) {
    let val =  (!this.parseError) ? null : {
      jsonParseError: {
        valid: false,
      },
    };
    return val;
  }

  public registerOnChange(fn: any) {
    this.propagateChange = fn;

  }

  private onChange(event) {

    // get value from text area
    let newValue = event.target.value;

    try {
      // parse it to json
      this.data = JSON.parse(newValue);
      this.parseError = false;
      this.dataChanged.emit(this.data);
    } catch (ex) {
      // set parse error if it fails
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
