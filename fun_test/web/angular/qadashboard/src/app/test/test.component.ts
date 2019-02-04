import {Component, OnInit, Input, OnChanges} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

class Node {
  uId: number;  // unique Id
  scriptPath: string;
  childrenIds: number [] = [];
  indent: number = 0;
  show: boolean = false;
  expanded: boolean = false;
  leaf: boolean = false;
}

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})
export class TestComponent implements OnInit, OnChanges {
  data: any = {};
  parsedData: any = {};
  uId = 0;
  flatNodes: Node [] = [];
  nodeIdMap: any = {};
  singleSelectNode = null;

  constructor(private apiService: ApiService, private logger: LoggerService) {
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


  getUid() {
    return this.uId++;
  }

  ngOnInit() {
    this.data = ["examples/vanilla.py", "networking/script1.py", "networking/qos/script2.py"];
    this.parseIt();
  }

  ngOnChanges(){
  }

  addFlatNode() {

  }

  addParts(remainingParts, parsedDataReference, show=false) {
    parsedDataReference.children[remainingParts[0]] = {indent: parsedDataReference.indent + 1};
    let newReference = parsedDataReference.children[remainingParts[0]];
    let newNode = new Node();
    newNode.scriptPath = remainingParts[0];
    newNode.uId = this.getUid();
    newNode.indent = parsedDataReference.indent + 1;
    newNode.show = show;
    if (newNode.scriptPath.endsWith(".py")) {
      newNode.leaf = true;
    }
    this.nodeIdMap[newNode.uId] = newNode;
    this.flatNodes.push(newNode);

    if (remainingParts.length > 1) {
      newReference["children"] = {};
      let newArray = remainingParts.slice(1, remainingParts.length);
      newNode.childrenIds.push(this.addParts(newArray, newReference).uId);
    }
    return newNode;
  }

  collapse(node, doCollapse=false) {
    /*if (node.indent > 1) { // cannot collapse the first level
      node.show = false;
    }*/

    if (doCollapse) {
      node.show = false;
    }

    for (let index = 0; index < node.childrenIds.length; index++) {
      this.collapse(this.nodeIdMap[node.childrenIds[index]], true);
    }
    node.expanded = false;
  }

  expand(node) {
    node.show = true;

    for (let index = 0; index < node.childrenIds.length; index++) {
      this.nodeIdMap[node.childrenIds[index]].show = true;
    }
    node.expanded = true;
  }

  getIndents(node) {
    return Array(node.indent);
  }

  parseIt() {
    this.parsedData["root"] = {indent: 0, children: {}};
    let rootNode = new Node();
    rootNode.scriptPath = "root";
    rootNode.uId = this.getUid();
    for (let index = 0; index < this.data.length; index++) {
      let parts = this.data[index].split("/");
      rootNode.childrenIds.push(this.addParts(parts, this.parsedData["root"], true).uId);
    }

    let i = 0;

  }

}
