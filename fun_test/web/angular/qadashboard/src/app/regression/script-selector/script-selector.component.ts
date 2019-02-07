import {Component, EventEmitter, OnInit, OnChanges, Input, Output} from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {LoggerService} from "../../services/logger/logger.service";

class Node {
  uId: number;  // unique Id
  scriptPath: string;
  pk: number = null;
  childrenIds = null;
  indent: number = 0;
  show: boolean = false;
  expanded: boolean = false;
  leaf: boolean = false;
}


@Component({
  selector: 'app-script-selector',
  templateUrl: './script-selector.component.html',
  styleUrls: ['./script-selector.component.css']
})
export class ScriptSelectorComponent implements OnInit, OnChanges {
  data: any = {};
  parsedData: any = {};
  uId = 0;
  flatNodes: Node [] = [];
  nodeIdMap: any = {};
  singleSelectNode = null;
  selectionMode = false;
  savedSingleSelectNode = null;
  @Input() resetEvent: any = null;
  @Output() singleSelectPk: EventEmitter<number> = new EventEmitter();


  constructor(private apiService: ApiService, private logger: LoggerService) {
  }

  fetchScripts() {
    this.apiService.get('/regression/scripts').subscribe(response => {
      this.data = response.data;
      this.parseIt();
    }, error => {
      this.logger.error('/regression/scripts');
    })
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

  selectClick () {
    this.selectionMode = !this.selectionMode;
  }

  getUid() {
    return this.uId++;
  }

  ngOnInit() {
    //this.data = ["examples/vanilla.py", "networking/script1.py", "networking/qos/script2.py"];
    this.fetchScripts();

  }

  ngOnChanges(){
  }

  addFlatNode() {

  }

  addParts(remainingParts, parsedDataReference, pk, show=false) {
    let firstToken = remainingParts[0];
    let thisNode = null;
    if (!parsedDataReference.children.hasOwnProperty(firstToken)) {
      parsedDataReference.children[firstToken] = {indent: parsedDataReference.indent + 1};
      let newNode = new Node();
      newNode.scriptPath = firstToken;
      newNode.uId = this.getUid();
      newNode.indent = parsedDataReference.indent + 1;
      newNode.show = show;
      newNode.childrenIds = new Set();
      if (newNode.scriptPath.endsWith(".py")) {
        newNode.leaf = true;
        newNode.pk = pk;
      }
      parsedDataReference.children[firstToken]["uId"] = newNode.uId;
      this.nodeIdMap[newNode.uId] = newNode;
      //this.flatNodes.push(newNode);
    }
    thisNode = this.nodeIdMap[parsedDataReference.children[firstToken].uId];
    let newReference = parsedDataReference.children[firstToken];
    if (remainingParts.length > 1) {
      if (!newReference.hasOwnProperty("children")) {
        newReference["children"] = {};
      }

      let newArray = remainingParts.slice(1, remainingParts.length);
      thisNode.childrenIds.add(this.addParts(newArray, newReference, pk).uId);
    }
    return thisNode;
  }

  collapse(node, doCollapse=false) {
    if (doCollapse) {
      node.show = false;
    }

    this.nodeIdMap[node.uId].childrenIds.forEach(childId => {
      this.collapse(this.nodeIdMap[childId], true);
    });
    node.expanded = false;
  }

  expand(node) {
    node.show = true;

    this.nodeIdMap[node.uId].childrenIds.forEach(childId => {
      this.nodeIdMap[childId].show = true;
    });
    node.expanded = true;
  }

  getIndents(node) {
    return Array(node.indent);
  }

  flattenNode (node) {
    this.flatNodes.push(node);
    node.childrenIds.forEach(childId => {
      this.flattenNode(this.nodeIdMap[childId]);
    });
  }

  parseIt() {
    this.parsedData["root"] = {indent: 0, children: {}};
    let rootNode = new Node();
    rootNode.scriptPath = "root";
    rootNode.uId = this.getUid();
    rootNode.childrenIds = new Set();
    for (let index = 0; index < this.data.length; index++) {
      let parts = this.data[index].script_path.split("/");
      let newArray = parts.slice(1, parts.length);
      let pk = this.data[index].pk;
      rootNode.childrenIds.add(this.addParts(newArray, this.parsedData["root"], pk,true).uId);
    }
    this.flattenNode(rootNode);
    let i = 0;

  }

  singleSelectClick(node) {
    this.singleSelectNode = node;
    if (this.singleSelectNode) {
      this.singleSelectPk.emit(this.singleSelectNode.pk);
    }
  }

}
