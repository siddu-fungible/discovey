export class ButtonType {
  static DELETE: 1;
}

export class GenericButton {
  text: string;
  constructor(props) {
    if (props.hasOwnProperty('text')) {
      this.text = props.text;
    }
  }
}

export class FunButtonWithIcon extends GenericButton {
  type: ButtonType;
  callback: Function;
  classes: string = "";
  textClasses: string = "";
  constructor(props) {
    super(props);
    if (props.hasOwnProperty('type')) {
      this.type = props.type;
      if (this.type === ButtonType.DELETE) {
        this.classes += `${this.classes} fa-trash`;
        this.textClasses += `${this.textClasses} text-color-red`;
      }
    }
    if (props.hasOwnProperty('callback')) {
      this.callback = props.callback;
    }

  }
}
