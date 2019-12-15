export class ButtonType {
  static DELETE: 1;
}

export class GenericButton {
  text: string;
  callback: Function = null;
  type: ButtonType;
  classes: string = "";
  textClasses: string = "";

  constructor(props) {
    if (props.hasOwnProperty('text')) {
      this.text = props.text;
    }
    if (props.hasOwnProperty('callback')) {
      this.callback = props.callback;
    }
  }
}

export class FunButtonWithIcon extends GenericButton {
  constructor(props) {
    super(props);
    if (props.hasOwnProperty('type')) {
      this.type = props.type;
      if (this.type === ButtonType.DELETE) {
        this.classes += `${this.classes} fa-trash`;
        this.textClasses += `${this.textClasses} text-color-red`;
      }
    }
  }
}

export class FunActionLink {
  text: string;
  callback: Function = null;
  data: any = null;
  show: boolean = true;
  constructor(props) {
    if (props.hasOwnProperty('text')) {
      this.text = props.text;
    }
    if (props.hasOwnProperty('callback')) {
      this.callback = props.callback;
    }
    if (props.hasOwnProperty('show')) {
      this.show = props.show;
    }
  }
}

