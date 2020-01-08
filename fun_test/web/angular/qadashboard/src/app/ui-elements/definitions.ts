export class ButtonType {
  static DELETE: number = 1;
  static LINK: number = 2;
}

export class GenericButton {
  text: string;
  callback: Function = null;
  type: ButtonType;
  classes: string = "";
  textClasses: string = "";
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
    if (props.hasOwnProperty('type')) {
      this.type = props.type;
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
      if (this.type === ButtonType.LINK) {
        this.classes += `${this.classes}`;
        this.textClasses += `${this.textClasses} fun-action-link`;
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

