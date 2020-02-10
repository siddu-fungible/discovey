import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {RegressionService} from "../../regression/regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";
import {ApiResponse, ApiService} from "../../services/api/api.service";
import {CommonService} from "../../services/common/common.service";
import {UserService} from "../../services/user/user.service";
import {LoggerService} from "../../services/logger/logger.service";
import {TreeNode} from "./definitions";

class FlatNode {
  name: string = null;
  leaf: boolean = false;
  id: number;
  lineage: number[] = [];
  collapsed: boolean = true;
  hide: boolean = true;
  treeNode: TreeNode = null;
  indent: number = 0;
  highlight: boolean = false;
  children: FlatNode[] = [];

  addChild(childNode) {
    this.children.push(childNode);
  }
}

@Component({
  selector: 'app-tree',
  templateUrl: './tree.component.html',
  styleUrls: ['./tree.component.css']
})

export class TreeComponent implements OnInit {
  @Input() tree: any = null;
  @Output() clickedStatsTreeNode: EventEmitter<any> = new EventEmitter();
  users: any = null;
  flatNodes: FlatNode[] = [];
  currentFlatNode: FlatNode = null;

  constructor(private regressionService: RegressionService,
              private apiService: ApiService,
              private loggerService: LoggerService,
              private commonService: CommonService,
              private userService: UserService
  ) {

  }

  ngOnInit() {
    let treeNode = this.tree;
    if (this.tree) {
      let flatNode = new FlatNode();
      flatNode.name = treeNode.name;
      flatNode.leaf = treeNode.leaf;
      flatNode.id = treeNode.id;
      flatNode.lineage.push(treeNode.id);
      flatNode.treeNode = treeNode;
      flatNode.indent = 0;
      flatNode.hide = false;
      flatNode.collapsed = false;
      this.flatNodes.push(flatNode);
      if (this.tree.children) {
        this.tree.children.forEach(thisChildNode => {
          let flatNodeChild = this.addChild(thisChildNode, flatNode);
          flatNodeChild.hide = false;
          flatNode.addChild(flatNodeChild);
          //this.flatNodes.push(flatNodeChild);

        })
      }
    }
  }


  addChild(childNode, parentFlatNode) {
    let flatNode = new FlatNode();
    this.flatNodes.push(flatNode);
    flatNode.name = childNode.name;
    flatNode.leaf = childNode.leaf;
    flatNode.id = childNode.id;
    for (let linId of parentFlatNode.lineage) {
      flatNode.lineage.push(linId);
    }
    flatNode.lineage.push(childNode.id);
    flatNode.treeNode = childNode;
    flatNode.indent = parentFlatNode.indent + 1;
    flatNode.hide = true;
    if (childNode.children) {
      childNode.children.forEach(thisChildNode => {
        flatNode.addChild(this.addChild(thisChildNode, flatNode));
      })
    }
    return flatNode;
  }


  clickNode(flatNode) {
    if (this.currentFlatNode) {
      this.currentFlatNode.highlight = false;
    }
    flatNode.highlight = true;
    this.currentFlatNode = flatNode;
    if (!flatNode.leaf) {
      flatNode.collapsed = !flatNode.collapsed;
      for (let child of flatNode.children) {
        if (child.hide) {
          this.expandNode(child);
        } else {
          this.collapseNode(child);
        }
      }
    } else {
      flatNode.treeNode.checked = !flatNode.treeNode.checked;
      this.clickedStatsTreeNode.emit(flatNode);
    }
  }

  expandNode(node): void {
    node.hide = false;
  }

  collapseNode(node): void {
    if (!node.leaf) {
      node.collapsed = true;
      for (let child of node.children) {
        this.collapseNode(child);
      }
    }
    node.hide = true;
  }

  getIndentHtml = (node) => {
    let s = "";
    if (node.hasOwnProperty("indent")) {
      for (let i = 0; i < node.indent - 1; i++) {
        s += "<span style=\"color: whitesmoke\">&rarr;</span>";
      }
      if (node.indent)
        s += "<span>&nbsp;&nbsp;</span>";
    }

    return s;
  };

}
