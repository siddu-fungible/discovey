import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../../services/api/api.service";
import {LoggerService} from "../../../services/logger/logger.service";
import {Title} from "@angular/platform-browser";


class ChildInfo {
  lastScore: number;
  weight: number;
  weightEditing: boolean = false;
  weightBeingEdited: number;
}

class Node {
  metricId: number;
  leaf: boolean;
  chartName: string;
  metricModelName: string;
  numLeaves: number;
  childrenInfo: Map<number, ChildInfo> = new Map<number, ChildInfo>();
  childrenScoreMap: Map<number, number> = new Map();
  childrenWeights: Map<number, number> = new Map();
  children: number[] = [];
  showAddChart: boolean = false;
}

class FlatNode {
  gUid: number;
  node: Node;
  collapsed: boolean;
  hide: boolean;
  indent: number;
  children: FlatNode[] = [];
  lineage: any = [];

  addChild(flatNode: FlatNode) {
    this.children.push(flatNode);
  }
}

enum Mode {
  None,
  ShowingAtomicMetric,
  ShowingNonAtomicMetric,
  ShowingBugPanel
}

@Component({
  selector: 'app-admin-dag',
  templateUrl: './admin-dag.component.html',
  styleUrls: ['./admin-dag.component.css']
})

export class AdminDagComponent implements OnInit {
  mode: Mode = Mode.None;
  metricMap: any;
  cachedNodeInfo: any;
  goodnessTrendValues: any;
  inner: any;
  childData: any;
  dag: any = null;
  nodeMap: Map<number, Node> = new Map<number, Node>();  // Metric Id to node
  guIdFlatNodeMap = {};

  lastGuid: number = 0;
  flatNodes: FlatNode[] = [];
  currentFlatNode: FlatNode = null;
  currentNode: Node = null;
  modeType = Mode;
  currentNodeInfo: string;
  status: string = null;

  chartReady: boolean = false;

  f1Node: FlatNode = null;
  s1Node: FlatNode = null;
  allMetricsNode: FlatNode = null;

  constructor(
    private apiService: ApiService,
    private loggerService: LoggerService,
    private title: Title
  ) {
  }

  ngOnInit() {
    console.log("Component Init");
    this.title.setTitle('Edit Dag');
    this.status = "Loading";
    this.fetchDag();
    this.status = null;

  }

  getGuid(): number {
    this.lastGuid++;
    return this.lastGuid;
  }


  fetchDag(): void {
    // Fetch the DAG
    this.apiService.get("/metrics/dag").subscribe(response => {
      this.dag = response.data;
      let lineage = [];
      for (let dag of this.dag) {
        this.walkDag(dag, lineage);
      }
      this.f1Node = this.flatNodes[0];
      this.f1Node.hide = false;
      this.expandNode(this.f1Node);
      this.expandNode(this.s1Node);
    }, error => {
      this.loggerService.error("fetchDag");
    });
  }

  getNodeFromEntry(metricId: number, dagEntry: any): Node {
    let node = new Node();
    node.metricId = metricId;
    node.leaf = dagEntry.leaf;
    node.chartName = dagEntry.chart_name;
    node.metricModelName = dagEntry.metric_model_name;
    node.numLeaves = dagEntry.num_leaves;
    node.children = dagEntry.children;
    node.showAddChart = false;
    Object.keys(dagEntry.children_weights).forEach((key) => {
      let childInfo: ChildInfo = new ChildInfo();
      childInfo.weight = dagEntry.children_weights[Number(key)];
      childInfo.weightEditing = false;
      childInfo.lastScore = dagEntry.children_info[Number(key)].last_two_scores[0];
      node.childrenInfo.set(Number(key), childInfo);
    });
    let keys = Array.from(node.childrenInfo.keys());
    return node;
  }


  getNode = (id) => {
    let node = this.nodeMap.get(id);
    return node;
  };

  addNodeToMap(metricId: number, node: Node): void {
    this.nodeMap.set(Number(metricId), node);
  }

  getNewFlatNode(node: Node, indent: number): FlatNode {
    let newFlatNode = new FlatNode();
    newFlatNode.gUid = this.getGuid();
    newFlatNode.node = node;
    newFlatNode.hide = true;
    newFlatNode.collapsed = true;
    newFlatNode.indent = indent;
    return newFlatNode;
  }

  walkDag(dagEntry: any, lineage: any, indent: number = 0): void {
    let thisFlatNode = null;
    //this.loggerService.log(dagEntry);
    let numMetricId: number = dagEntry["metric_id"]; // TODO, why do we need this conversion
    let nodeInfo = dagEntry;
    let newNode = this.getNodeFromEntry(numMetricId, dagEntry);
    this.addNodeToMap(numMetricId, newNode);
    thisFlatNode = this.getNewFlatNode(newNode, indent);
    if (newNode.chartName === "S1") {
      thisFlatNode.hide = false;
      this.s1Node = thisFlatNode;
      lineage = [];
    }
    this.guIdFlatNodeMap[thisFlatNode.gUid] = thisFlatNode;
    this.flatNodes.push(thisFlatNode);
    let parentsGuid = {};
    parentsGuid["guid"] = thisFlatNode.gUid;
    parentsGuid["chartName"] = newNode.chartName;
    lineage.push(parentsGuid);
    thisFlatNode.lineage = [lineage.slice()];
    if (!nodeInfo.leaf) {
      let children = nodeInfo.children;

      children.forEach((cId) => {
        let childEntry = nodeInfo.children_info[Number(cId)];
        let childFlatNode = this.walkDag(childEntry, lineage.slice(), indent + 1);
        thisFlatNode.addChild(childFlatNode);
      });
    }
    return thisFlatNode;
  }


  collapseBranch = (flatNode) => {
    flatNode.children.forEach((child) => {
      child.hide = true;
      child.collapsed = true;
      this.collapseBranch(child);
    });
  };

  collapseNode = (flatNode) => {
    flatNode.collapsed = true;
    this.collapseBranch(flatNode);
  };

  getVisibleNodes = () => {
    return this.flatNodes.filter(flatNode => {
      return !flatNode.hide
    })
  };

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

  openUrl(url): void {
    window.open(url, '_blank');
  }

  guid = () => {
    function s4() {
      return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
    }

    return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
  };

  expandNode = (flatNode, all = false) => {
    let topLineage = null;
    if (flatNode.hasOwnProperty("lineage")) {
      if (flatNode.lineage.length > 0) {
        topLineage = flatNode.lineage[0];
      }
    }
    if (topLineage) {
      for (let index = 0; index < topLineage.length - 1; index++) {
        //this.expandNode(topLineage[index]);
        let thisNode = this.guIdFlatNodeMap[topLineage[index].guid];
        this.expandNode(thisNode);
        //thisNode.hide = false;
        //thisNode.collapsed = false;
      }
    }

    flatNode.collapsed = false;
    flatNode.hide = false;
    flatNode.children.forEach((child) => {
      child.hide = false;
    });
  };

  showAtomicMetric = (flatNode) => {
    this.mode = Mode.ShowingAtomicMetric;
    if (this.currentFlatNode)
      this.currentFlatNode.node.showAddChart = false;
  };


  showNonAtomicMetric = (flatNode) => {
      this.mode = Mode.ShowingNonAtomicMetric;
      this.expandNode(flatNode);
      if (this.currentFlatNode)
        this.currentFlatNode.node.showAddChart = false;
      this.currentFlatNode = flatNode;
      flatNode.node.showAddChart = true;
  };

  addChart(flatNode): void {
    console.log();

  }

}
