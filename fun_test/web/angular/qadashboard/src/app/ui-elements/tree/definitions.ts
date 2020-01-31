export class TreeNode {
  id: number;
  name: string;
  leaf: boolean;
  meta_data: any = {};
  checked: boolean = false;
  children: TreeNode [] = null;

  constructor(props) {
    this.name = props.name;
    this.leaf = props.leaf;
    this.id = props.id;
  }

  addChild(node: TreeNode) {
    if (!this.children) {
      this.children = [];
    }
    this.children.push(node);
    return node;
  }
}
