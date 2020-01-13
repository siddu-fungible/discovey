import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {RegressionService} from "../regression/regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";
import {ApiResponse, ApiService} from "../services/api/api.service";
import {CommonService} from "../services/common/common.service";
import {TestBedService} from "../regression/test-bed/test-bed.service";
import {UserService} from "../services/user/user.service";
import {LoggerService} from "../services/logger/logger.service";
import {Tree} from "@angular/router/src/utils/tree";

class TreeNode {
  id: number;
  name: string;
  meta_data: any = null;
  children: TreeNode [] = null;

  constructor(props) {
    this.name = props.name;
  }

  addChild(node: TreeNode) {
    if (!this.children) {
      this.children = [];
    }
    this.children.push(node);
    return node;
  }
}

enum EditMode {
  NONE = 0,
  MANUAL_LOCK_INITIAL = "Set manual lock",
  MANUAL_LOCK_UPDATE_EXPIRATION = "Update manual lock expiration"
}

class FlatNode {
  name: string = null;
  leaf: boolean = false;
  hide: boolean = true;
  indent: number = 0;
  children: FlatNode[] = [];
}

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css'],
})

export class TestComponent implements OnInit {

  @Input() data: any = null;
  @Output() clickedNode: EventEmitter<any> = new EventEmitter();
  @Input() embed: boolean = false;
  schedulingTime = {hour: 1, minute: 1};
  testBeds: any [] = null;
  automationStatus = {};
  manualStatus = {};
  assetLevelManualLockStatus = {};
  currentEditMode: EditMode = EditMode.NONE;
  currentTestBed: any = null;
  EditMode = EditMode;
  users: any = null;
  lockPanelHeader: string = null;
  selectedUser: any = null;
  assetSelectedUser: any = null;
  assets = null;
  driver = null;
  refreshing: string = null;
  userMap: any = null;
  editingDescription: boolean = false;
  currentDescription: string;
  flatNodes: FlatNode[] = [];
  tree: TreeNode = null;

  constructor(private regressionService: RegressionService,
              private apiService: ApiService,
              private loggerService: LoggerService,
              private commonService: CommonService,
              private service: TestBedService,
              private userService: UserService
  ) {
    this.tree = new TreeNode({name: "root"});
    let systemNode = this.tree.addChild(new TreeNode({name: "system"}));
    let storageNode = this.tree.addChild(new TreeNode({name: "storage"}));
    systemNode.addChild(new TreeNode({name: "BAM"}));
    systemNode.addChild(new TreeNode({name: "VP utilization"}));
    storageNode.addChild(new TreeNode({name: "SSD"}));

  }

  ngOnInit() {

    let treeNode = this.tree;
    if (this.tree) {
      let flatNode = new FlatNode();
      flatNode.name = treeNode.name;
      this.flatNodes.push(flatNode);
      flatNode.indent = 0;
      flatNode.hide = false;
      if (this.tree.children) {
        this.tree.children.forEach(thisChildNode => {
          this.addChild(this.tree, thisChildNode, flatNode.indent);
        })
      }
      let u = 0;
    }
  }


  addChild(parentNode, childNode, parentsIndent) {
    let flatNode = new FlatNode();
    this.flatNodes.push(flatNode);
    flatNode.name = childNode.name;
    flatNode.indent = parentsIndent + 1;
    flatNode.hide = false;
    if (childNode.children) {
      childNode.children.forEach(thisChildNode => {
        this.addChild(childNode, thisChildNode, flatNode.indent);
      })
    }
  }

  /*setFlatNodes(d, node, indent): FlatNode {
    if (!d["leaf"]) {
      for (let child of d["children"]) {
        let flatNode = new FlatNode();
        flatNode.name = child["name"];
        flatNode.leaf = child["leaf"];
        flatNode.children = [];
        flatNode.indent = indent + 1;
        this.flatNodes.push(flatNode);
        let childFlatNode = this.setFlatNodes(child, flatNode, indent + 1);
        node.children.push(childFlatNode);
      }
    }
    return node;
  }*/

  clickNode(flatNode) {
    if (!flatNode.leaf) {
      for (let child of flatNode.children) {
        if (child.hide) {
          this.expandNode(child);
        } else {
          this.collapseNode(child);
        }
      }
    } else {
      this.clickedNode.emit(flatNode);
    }
  }

  expandNode(node): void {
    node.hide = false;
  }

  collapseNode(node): void {
    if (!node.leaf) {
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
        s += "<span style=\"color: white\">&rarr;</span>";
      }
      if (node.indent)
        s += "<span>&nbsp;&nbsp;</span>";
    }

    return s;
  };

}
