import {Component, OnInit} from '@angular/core';
import {Location} from '@angular/common';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

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
  numChildrenFailed: number;
  numChildrenDegrades: number;
  lastNumBuildFailed: number;
  numLeaves: number;
  scores: any;
  childrenInfo: Map<number, ChildInfo> = new Map<number, ChildInfo>();
  childrenScoreMap: Map<number, number> = new Map();
  childrenWeights: Map<number, number> = new Map();
  trend: number;
  lastScore: number = null;
  children: number[] = [];
  last_two_scores: number[] = [];
  grid: any[];
  copiedScore: boolean = false;
  copiedScoreDisposition: number = null;
}

class FlatNode {
  gUid: number;
  node: Node;
  collapsed: boolean;
  hide: boolean;
  indent: number;
  children: FlatNode[] = [];

  addChild(flatNode: FlatNode) {
    this.children.push(flatNode);
  }
}

enum Mode {
  None,
  ShowingAtomicMetric,
  ShowingNonAtomicMetric
}

@Component({
  selector: 'app-performance',
  templateUrl: './performance.component.html',
  styleUrls: ['./performance.component.css']
})
export class PerformanceComponent implements OnInit {
  numGridColumns: number;
  lastStatusUpdateTime: any;
  mode: Mode = Mode.None;
  metricMap: any;
  cachedNodeInfo: any;
  goodnessTrendValues: any;
  inner: any;
  childData: any;
  dag: any = null;
  nodeMap: Map<number, Node> = new Map<number, Node>();
  lastGuid: number = 0;
  flatNodes: FlatNode[] = [];
  currentNode: Node = null;
  modeType = Mode;
  currentNodeInfo: string;
  showScoreInfo: boolean = false;
  miniGridMaxWidth: string;

  constructor(
    private location: Location,
    private apiService: ApiService,
    private loggerService: LoggerService
  ) {
  }

  ngOnInit() {
    let myMap = new Map().set('a', 1).set('b', 2);
    let keys = Array.from(myMap.keys());
    console.log(keys);
    this.numGridColumns = 2;
    this.miniGridMaxWidth = '50%';
    this.fetchDag();
    if (window.screen.width >= 1690) {
      this.numGridColumns = 4;
      this.miniGridMaxWidth = '25%';
    }
  }

  getGuid(): number {
    this.lastGuid++;
    return this.lastGuid;
  }

  fetchDag(): void {
    // Fetch the DAG
    let payload: { [i: string]: string } = {metric_model_name: "MetricContainer", chart_name: "Total"};
    this.apiService.post("/metrics/dag", payload).subscribe(response => {
      this.dag = response.data;
      this.walkDag(this.dag);
      this.flatNodes[0].hide = false;
      this.expandNode(this.flatNodes[0]);
      let i = 0;
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
    node.numChildrenDegrades = dagEntry.last_num_degrades;
    node.lastNumBuildFailed = dagEntry.last_num_build_failed;
    node.children = dagEntry.children;
    node.last_two_scores = dagEntry.last_two_scores;
    node.copiedScore = dagEntry.copied_score;
    node.copiedScoreDisposition = dagEntry.copied_score_disposition;

    Object.keys(dagEntry.children_weights).forEach((key) => {
      let childInfo: ChildInfo = new ChildInfo();
      childInfo.weight = dagEntry.children_weights[Number(key)];
      childInfo.weightEditing = false;
      childInfo.lastScore = dagEntry.children_info[Number(key)].last_two_scores[0];
      node.childrenInfo.set(Number(key), childInfo);
    });
    this.fetchScores(node);
    let keys = Array.from(node.childrenInfo.keys());
    return node;
  }

  getKeys(map) {
    //console.log(map.keys());
    let a = Array.from(map.keys());
    return a;
  }

  getSumChildWeights = (currentNode) => {
    let sumOfWeights = 0;
    currentNode.childrenInfo.forEach((childInfo, key) => {
      sumOfWeights += childInfo.weight;
    });
    return sumOfWeights;
  };

  getScoreTotal = (currentNode) => {
    let children = currentNode.children;
    let scoreTotal = 0;
    currentNode.childrenInfo.forEach((childInfo, key) => {
      scoreTotal += childInfo.weight * (childInfo.lastScore || 0);
    });
    return scoreTotal;
  };

  fetchScores(node) {
    let dateRange = this.getDateRange();
    let fromDate = dateRange[0];
    let toDate = dateRange[1];
    let payload = {metric_id: node.metricId, date_range: [fromDate.toISOString(), toDate.toISOString()]};
    payload.metric_id = node.metricId;
    this.evaluateScores(node);
    return node;
  }

  getNode = (id) => {
    let node = this.nodeMap.get(id);
    return node;
  };

  evaluateScores = (node) => {
    let [lastScore, penultimateScore] = node.last_two_scores;
    //lastScore = lastScore;
    node.lastScore = lastScore;
    try {

      node.trend = 0;
      if (lastScore < penultimateScore) {
        node.trend = -1;
      }
      if (lastScore > penultimateScore) {
        node.trend = 1;
      }
      node.lastScore = lastScore;
    } catch (e) {
    }
    if (node.copiedScore) {
      if (node.copiedScoreDisposition > 0) {
        node.trend = 1;
      } else if (node.copiedScoreDisposition < 0) {
        node.trend = -1;
      }
    }

  };

  prepareGridNodes = (node) => {
    node.grid = [];
    let maxRowsInMiniChartGrid = 10;
    let maxColumns = this.numGridColumns;
    console.log("Prepare Grid nodes");
    let tempGrid = [];
    let rowIndex = 0;
    let childNodes = [];
    node.childrenInfo.forEach((childInfo, childId) => {
      childNodes.push(this.nodeMap.get(Number(childId)));
    });

    let oneRow = [];
    childNodes.forEach((childNode) => {
      oneRow.push(childNode);
      if (oneRow.length === maxColumns) {
        node.grid.push(oneRow);
        oneRow = [];
      }
    });
    if (oneRow.length) {
      node.grid.push(oneRow);
    }
  };

  getCurrentNodeScoreInfo = (node) => {
    this.currentNodeInfo = null;
    if (node.metricModelName !== 'MetricContainer') {
      //$scope.showingContainerNodeInfo = !$scope.showingContainerNodeInfo;
      if (node.positive) {
        this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(last actual value/expected value) * 100&nbsp)/n";
      } else {
        this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(expected value/last actual value) * 100&nbsp)/n";
      }
      this.currentNodeInfo += "&nbsp, where n is the number of data-sets";
    }
    return this.currentNodeInfo;
  };

  showScoreInfoClick = (node) => {
    this.showScoreInfo = !this.showScoreInfo;


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

  walkDag(dagEntry: object, indent: number = 0): void {
    let thisFlatNode = null;
    //this.loggerService.log(dagEntry);
    for (let metricId in dagEntry) {
      let numMetricId: number = Number(metricId); // TODO, why do we need this conversion
      let nodeInfo = dagEntry[numMetricId];
      let newNode = this.getNodeFromEntry(numMetricId, dagEntry[numMetricId]);
      this.addNodeToMap(numMetricId, newNode);
      thisFlatNode = this.getNewFlatNode(newNode, indent);
      this.flatNodes.push(thisFlatNode);
      //this.loggerService.log('Node:' + nodeInfo.chart_name);
      if (!nodeInfo.leaf) {
        let children = nodeInfo.children;
        children.forEach((cId) => {
          //let childEntry: {[childId: number]: object} = {cId: nodeInfo.children_info[Number(childId)]};
          let childEntry = {[cId]: nodeInfo.children_info[Number(cId)]};
          let childFlatNode = this.walkDag(childEntry, indent + 1);
          thisFlatNode.addChild(childFlatNode);
        })
      }
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

  space = (number) => {
    let s = "";
    for (let i = 0; i < number; i++) {
      s += "&nbsp";
    }
    return s;
  };

  getVisibleNodes = () => {
    return this.flatNodes.filter(flatNode => {
      return !flatNode.hide
    })
  };

  setValues(pageNumber): void {
  }

  goBack(): void {
    this.location.back();
  }

  getLastStatusUpdateTime() {
    this.apiService.get('/common/time_keeper/' + "last_status_update").subscribe((data) => {
      this.lastStatusUpdateTime = data;
    }, error => {

    });
  }


  fetchRootMetricInfo(chartName, metricModelName): any {
    let payload = {"metric_model_name": metricModelName, chart_name: chartName};
    this.apiService.post('/metrics/chart_info', payload).subscribe((data) => {
      return data;
    }, error => {
      this.loggerService.error("fetchRootMetricInfo");
    });
  }

  populateNodeInfoCache(data) {
    if (!(data.metric_id in this.cachedNodeInfo)) {
      this.cachedNodeInfo[data.metric_id] = data;
    }
    data.children_info.forEach((value, key) => {
      this.cachedNodeInfo[key] = value;
      value.children_info.forEach((v2, key2) => {
        this.populateNodeInfoCache(v2);
      });
    });
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

  editingWeightClick = (info) => {
    info.weightEditing = true;
    info.weightBeingEdited = info.weight;
  };


  getDateBound = (dt, lower) => {
    let newDay = new Date(dt);
    if (lower) {
      newDay.setHours(0, 0, 1);
    } else {
      newDay.setHours(23, 59, 59);
    }

    return newDay;
  };

  isSameDay(d1, d2) {
    return d1.getFullYear() === d2.getUTCFullYear() &&
      d1.getUTCMonth() === d2.getUTCMonth() &&
      d1.getUTCDate() === d2.getUTCDate();
  }

  getYesterday = (today) => {
    let yesterday: Date = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    return yesterday;
  };


  getDateRange = () => {
    let today = new Date();
    let startMonth = 4 - 1;
    let startDay = 1;
    let startMinute = 59;
    let startHour = 23;
    let startSecond = 1;
    let fromDate = new Date(today.getFullYear(), startMonth, startDay, startHour, startMinute, startSecond);
    fromDate = this.getDateBound(fromDate, true);
    let yesterday = this.getYesterday(today);
    let toDate = new Date(yesterday);
    toDate = this.getDateBound(toDate, false);
    return [fromDate, toDate];

  };

  getStatusHtml = (node) => {
    let s = "";
    if (node.leaf) {
      if (node.lastNumBuildFailed > 0) {
        s = "Bld: <label class=\"badge badge-danger\">FAILED</label>";
      }
    } else {

      if (node.numChildrenDegrades) {
        s += "<span style='color: red'><i class='fa fa-arrow-down aspect-trend-icon fa-icon-red'>:</i></span>" + node.numChildrenDegrades + "";
      }
      if (node.lastNumBuildFailed) {
        if (node.numChildrenDegrades) {
          s += ",&nbsp";
        }
        s += "<span style='color: red'><i class='fa fa-times fa-icon-red'>:</i></span>" + "<span style='color: black'>" + node.lastNumBuildFailed + "</span>";
      }
    }
    return s;
  };

  getNodeFromData = (data): any => {
    let newNode = {
      info: data.description,
      label: data.chart_name,
      collapsed: true,
      metricId: data.metric_id,
      hide: true,
      leaf: data.leaf,
      chartName: data.chart_name,
      metricModelName: data.metric_model_name,
      childrenWeights: JSON.parse(data.children_weights),
      children: {},
      lineage: [],
      numChildDegrades: data.last_num_degrades,
      positive: data.positive,
      numChildren: 0,
      numChildrenPassed: data.num_children_passed,
      numChildrenFailed: data.last_num_build_failed,
      lastBuildStatus: data.last_build_status,
      status: true

    };
    this.metricMap[newNode.metricId] = {chartName: newNode.chartName};
    if (newNode.info === "") {
      newNode.info = "<p>Please update the description</p>";
    }
    return newNode;
  };

  getTrendHtml = (node) => {
    let s = "";
    if (node.hasOwnProperty("trend")) {
      if (node.chartName === "All metrics") {
        node.trend = 0;
      }
      if (node.trend > 0) {
        s = "<span style='color: green'><icon class=\"fa fa-arrow-up aspect-trend-icon fa-icon-green\"></icon></span>&nbsp";
      } else if (node.trend < 0) {
        s = "<span style='color: red'><icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon></span>&nbsp;";
      }
      else if (node.trend === 0) {
        s = "<icon class=\"fa fa-arrow-down aspect-trend-icon\" style=\"visibility: hidden;\"></icon>&nbsp;";
      }
    }
    return s;
  };

  guid = () => {
    function s4() {
      return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
    }

    return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
  };

  openAtomicTab = () => {
        let url = "/upgrade/performance/atomic/" + this.currentNode.metricId;
        window.open(url, '_blank');
    };

  expandNode = (flatNode, all=false) => {
    flatNode.collapsed = false;
    flatNode.hide = false;
    flatNode.children.forEach((child) => {
      child.hide = false;
    })
  };

  showAtomicMetric = (flatNode) => {
    this.currentNode = flatNode.node;
    this.mode = Mode.ShowingAtomicMetric;
    this.expandNode(flatNode);
  };

  showNonAtomicMetric = (flatNode) => {
    this.currentNode = flatNode.node;
    this.mode = Mode.ShowingNonAtomicMetric;
    this.expandNode(flatNode);
    this.prepareGridNodes(flatNode.node);
  };

  submitWeightClick = (node, childId, info) => {
    let payload: { [i: string]: string } = {metric_id: node.metricId, child_id: childId, weight: info.weightBeingEdited};
    this.apiService.post('/metrics/update_child_weight', payload).subscribe((response) => {
      info.weight = info.weightBeingEdited;
    });
    info.weightEditing = false;
  };

  closeEditingWeightClick = (info) => {
         info.weightEditing = false;
     };


}
