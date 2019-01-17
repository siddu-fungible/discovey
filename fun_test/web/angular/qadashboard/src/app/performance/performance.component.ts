import {Component, OnInit, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {Title} from "@angular/platform-browser";
import {CommonService} from "../services/common/common.service";
import {ClipboardService} from 'ngx-clipboard';
import {Location} from '@angular/common';


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
  numBugs: number = 0;
  showAddJira: boolean = false;
  degrades: any = new Set();
  upgrades: any = new Set();
  failures: any = new Set();
  bugs: any = new Set();
}

class FlatNode {
  gUid: number;
  node: Node;
  collapsed: boolean;
  hide: boolean;
  indent: number;
  showJiraInfo: boolean = false;
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
  currentFlatNode: FlatNode = null;
  currentNode: Node = null;
  modeType = Mode;
  currentNodeInfo: string;
  showScoreInfo: boolean = false;
  miniGridMaxWidth: string;
  miniGridMaxHeight: string;
  status: string = null;

  currentRegressionUrl: string = null;
  currentJenkinsUrl: string = null;
  currentLsfUrl: string = null;
  currentGitCommit: string = null;
  passedRegressionUrl: string = null;
  passedJenkinsUrl: string = null;
  passedLsfUrl: string = null;
  passedGitCommit: string = null;
  failedRegressionUrl: string = null;
  failedJenkinsUrl: string = null;
  failedLsfUrl: string = null;
  failedGitCommit: string = null;

  failedDateTime: string = null;
  passedDateTime: string = null;
  gitDiagnose: boolean = false;

  lsfUrl: string = "http://palladium-jobs.fungible.local:8080/job/";
  jenkinsUrl: string = "http://jenkins-sw-master:8080/job/emulation/job/scheduled_emulation/";
  regressionUrl: string = "/regression/suite_detail/";

  globalSettings: any = null;
  private location: Location;
  toolTipMessage: string = null;
  @ViewChild('copyUrlTooltip') copyUrlTooltip;
  chartReady: boolean = false;
  lastScore: number;
  penultimateScore: number;
  deviation: any;

  upgradeFlatNode: FlatNode[] = [];
  degradeFlatNode: FlatNode[] = [];

  constructor(
    private apiService: ApiService,
    private loggerService: LoggerService,
    private title: Title,
    private commonService: CommonService,
    private clipboardService: ClipboardService
  ) {
  }

  ngOnInit() {
    this.title.setTitle('Performance');
    this.status = "Loading";
    let myMap = new Map().set('a', 1).set('b', 2);
    let keys = Array.from(myMap.keys());
    console.log(keys);
    this.numGridColumns = 2;
    this.miniGridMaxWidth = '50%';
    this.miniGridMaxHeight = '50%';
    this.fetchGlobalSettings();
    if (window.screen.width >= 1690) {
      this.numGridColumns = 4;
      this.miniGridMaxWidth = '25%';
      this.miniGridMaxHeight = '25%';
    }
    this.status = null;
  }

  getGuid(): number {
    this.lastGuid++;
    return this.lastGuid;
  }

  gitIdentify(): void {
    this.gitDiagnose = !this.gitDiagnose
  }

  fetchGlobalSettings(): void {
    this.apiService.get("/metrics/global_settings").subscribe(response => {
      this.globalSettings = response.data;
      this.fetchDag();
    }, error => {
      this.loggerService.error("fetchGlobalSettings");
    });
  }

  fetchDag(): void {
    // Fetch the DAG
    let payload: { [i: string]: string } = {metric_model_name: "MetricContainer", chart_name: "Total"};
    this.apiService.post("/metrics/dag", payload).subscribe(response => {
      this.dag = response.data;
      this.walkDag(this.dag);
      let upgradeNode = null;
      let node = new Node();
      node.chartName = "Up Since Previous";
      upgradeNode = this.getNewFlatNode(node, 0);
      upgradeNode.hide = false;
      this.flatNodes.push(upgradeNode);
      for (let upgradedChild of this.upgradeFlatNode) {
        upgradedChild.indent = 1;
        upgradeNode.addChild(upgradedChild);
      }
      let degradeNode = null;
      let node1 = new Node();
      node1.chartName = "Down Since Previous";
      degradeNode = this.getNewFlatNode(node1, 0);
      degradeNode.hide = false;
      degradeNode.node.chartName = "Down Since Previous";
      this.flatNodes.push(degradeNode);
      for (let degradeChild of this.degradeFlatNode) {
        degradeChild.indent = 1;
        degradeNode.addChild(degradeChild);
      }
      //total container should always appear
      this.flatNodes[0].hide = false;
      this.expandNode(this.flatNodes[0]);//expand total container on page load
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
    node.numBugs = dagEntry.jira_ids.length;
    node.showAddJira = false;

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

  calculateScores(node): void {
    let [lastScore, penultimateScore] = node.last_two_scores;
    this.lastScore = lastScore.toFixed(1);
    this.penultimateScore = penultimateScore.toFixed(1);
    let deviation = ((lastScore - penultimateScore) / (Math.min(lastScore, penultimateScore))) * 100;
    this.deviation = deviation.toFixed(1);
  }

  evaluateScores = (node) => {
    let [lastScore, penultimateScore] = node.last_two_scores;
    //lastScore = lastScore;
    node.lastScore = lastScore;
    try {

      node.trend = 0;
      let tolerancePercentage = 0;
      if (this.globalSettings) {
        tolerancePercentage = this.globalSettings.tolerance_percentage / 100;
      }
      if (lastScore < (penultimateScore * (1 - tolerancePercentage))) {
        node.trend = -1;
      }
      if (lastScore > (penultimateScore * (1 + tolerancePercentage))) {
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
    newFlatNode.showJiraInfo = false;
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
          let childNode = childFlatNode["node"];
          if (childNode.upgrades.size != 0) {
            childNode.upgrades.forEach(childMetricId => {
              thisFlatNode.node.upgrades.add(childMetricId);
            });
          }
          if (childNode.degrades.size != 0) {
            childNode.degrades.forEach(childMetricId => {
              thisFlatNode.node.degrades.add(childMetricId);
            });
          }
          if (childNode.failures.size != 0) {
            childNode.failures.forEach(childMetricId => {
              thisFlatNode.node.failures.add(childMetricId);
            });
          }
          if (childNode.bugs.size != 0) {
            childNode.bugs.forEach(childMetricId => {
              thisFlatNode.node.bugs.add(childMetricId);
            });
          }
          thisFlatNode.addChild(childFlatNode);
        })

      } else {
        let leafNode = thisFlatNode.node;
        if (leafNode.trend > 0) {
          if (!leafNode.upgrades.has(leafNode.metricId)) {
            leafNode.upgrades.add(leafNode.metricId);
          let flatNode = this.getNewFlatNode(leafNode, 1);
          this.upgradeFlatNode.push(flatNode);
          }

        } else if (leafNode.trend < 0) {
          if (!leafNode.degrades.has(leafNode.metricId)) {
            leafNode.degrades.add(leafNode.metricId);
          let flatNode = this.getNewFlatNode(leafNode, 1);
          this.degradeFlatNode.push(flatNode);
          }
        }
        if (leafNode.lastNumBuildFailed == 1) {
          leafNode.failures.add(leafNode.metricId);
        }
        if (leafNode.numBugs > 0) {
          leafNode.bugs.add(leafNode.metricId);
        }
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

  /*
  fetchRootMetricInfo(chartName, metricModelName): any {
    let payload = {"metric_model_name": metricModelName, chart_name: chartName};
    this.apiService.post('/metrics/chart_info', payload).subscribe((data) => {
      return data;
    }, error => {
      this.loggerService.error("fetchRootMetricInfo");
    });
  } */

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
    let tempNodes = this.getVisibleNodes();
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
    if (node.degrades.size != 0) {
      s += "<span style='color: red'><i class='fa fa-arrow-down aspect-trend-icon fa-icon-red'>:</i></span>" + node.degrades.size + "";
    }
    if (node.failures.size != 0) {
      if (node.degrades.size != 0) {
        s += "&nbsp";
      }
      s += "<span style='color: red'><i class='fa fa-times fa-icon-red'>:</i></span>" + "<span style='color: black'>" + node.failures.size + "</span>";
    }
    if (node.bugs.size != 0) {
      if (node.failures.size != 0 || node.degrades.size != 0) {
        s += "&nbsp";
      }
        s += "<span style='color: red'><i class='fa fa-bug'></i>:</span>" + "<span style='color: black'>" + node.bugs.size + "</span>";
    }
    return s;
  };

  setDefaultUrls(): void {
    this.currentRegressionUrl = null;
    this.currentJenkinsUrl = null;
    this.currentLsfUrl = null;
    this.currentGitCommit = null;
    this.passedRegressionUrl = null;
    this.passedJenkinsUrl = null;
    this.passedLsfUrl = null;
    this.passedGitCommit = null;
    this.failedRegressionUrl = null;
    this.failedJenkinsUrl = null;
    this.failedLsfUrl = null;
    this.failedGitCommit = null;
    this.failedDateTime = null;
    this.passedDateTime = null;
  }

  openTooltip(node): void {
    this.setDefaultUrls();
    //let payload = {"metric_model_name": node.metricModelName, chart_name: node.chartName};
    let payload = {"metric_id": node.metricId};
    this.apiService.post('/metrics/chart_info', payload).subscribe((data) => {
      let result = data.data;
      if (result.last_suite_execution_id && result.last_suite_execution_id !== -1) {
        this.currentRegressionUrl = this.regressionUrl + result.last_suite_execution_id;
      }
      if (result.last_jenkins_job_id && result.last_jenkins_job_id !== -1) {
        this.currentJenkinsUrl = this.jenkinsUrl + result.last_jenkins_job_id;
      }
      if (result.last_lsf_job_id && result.last_lsf_job_id !== -1) {
        this.currentLsfUrl = this.lsfUrl + result.last_lsf_job_id;
      }
      if (result.last_git_commit && result.last_git_commit !== "") {
        this.currentGitCommit = result.last_git_commit;
      }
    }, error => {
      this.loggerService.error("Current Failed Urls");
    });

    let payload1 = {"metric_id": node.metricId};
    this.apiService.post('/metrics/past_status', payload1).subscribe((data) => {
      let result = data.data;
      if (result.failed_date_time) {
        this.failedDateTime = result.failed_date_time;
      }
      if (result.failed_suite_execution_id && result.failed_suite_execution_id !== -1) {
        this.failedRegressionUrl = this.regressionUrl + result.failed_suite_execution_id;
      }
      if (result.failed_jenkins_job_id && result.failed_jenkins_job_id !== -1) {
        this.failedJenkinsUrl = this.jenkinsUrl + result.failed_jenkins_job_id;
      }
      if (result.failed_lsf_job_id && result.failed_lsf_job_id !== -1) {
        this.failedLsfUrl = this.lsfUrl + result.failed_lsf_job_id;
      }
      if (result.failed_git_commit && result.failed_git_commit !== "") {
        this.failedGitCommit = result.failed_git_commit;
      }
      if (result.passed_date_time) {
        this.passedDateTime = result.passed_date_time;
      }
      if (result.passed_suite_execution_id && result.passed_suite_execution_id !== -1) {
        this.passedRegressionUrl = this.regressionUrl + result.passed_suite_execution_id;
      }
      if (result.passed_jenkins_job_id && result.passed_jenkins_job_id !== -1) {
        this.passedJenkinsUrl = this.jenkinsUrl + result.passed_jenkins_job_id;
      }
      if (result.passed_lsf_job_id && result.passed_lsf_job_id !== -1) {
        this.passedLsfUrl = this.lsfUrl + result.passed_lsf_job_id;
      }
      if (result.passed_git_commit && result.passed_git_commit !== "") {
        this.passedGitCommit = result.passed_git_commit;
      }
    }, error => {
      this.loggerService.error("Past Status Urls");
    });

  }

  openUrl(url): void {
    window.open(url, '_blank');
  }

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
    let url = "/performance/atomic/" + this.currentNode.metricId;
    window.open(url, '_blank');
  };

  expandNode = (flatNode, all = false) => {
    flatNode.collapsed = false;
    flatNode.hide = false;
    flatNode.children.forEach((child) => {
      child.hide = false;
    })
  };

  expandUpgrades(): void{

  }

  expandDegrades(): void {

  }

  showAtomicMetric = (flatNode) => {
    this.chartReady = false;
    if (this.currentNode && this.currentNode.showAddJira) {
      this.currentNode.showAddJira = false;
    }
    if (this.currentFlatNode && this.currentFlatNode.showJiraInfo) {
      this.currentFlatNode.showJiraInfo = false;
    }
    this.currentNode = flatNode.node;
    this.currentFlatNode = flatNode;
    this.currentNode.showAddJira = true;
    this.mode = Mode.ShowingAtomicMetric;
    this.expandNode(flatNode);
    this.commonService.scrollTo("chart-info");
    this.chartReady = true;

  };

  showNonAtomicMetric = (flatNode) => {
    if(flatNode.node.metricModelName) {
      this.chartReady = false;
    if (this.currentNode && this.currentNode.showAddJira) {
      this.currentNode.showAddJira = false;
    }
    if (this.currentFlatNode && this.currentFlatNode.showJiraInfo) {
      this.currentFlatNode.showJiraInfo = false;
    }
    this.currentNode = flatNode.node;
    this.currentFlatNode = flatNode;
    this.mode = Mode.ShowingNonAtomicMetric;
    this.expandNode(flatNode);
    this.prepareGridNodes(flatNode.node);
    this.commonService.scrollTo("chart-info");
    this.chartReady = true;
    } else {
      this.chartReady = false;
      this.expandNode(flatNode);
      this.chartReady = true;
    }

  };

  submitWeightClick = (node, childId, info) => {
    let payload: { [i: string]: string } = {
      metric_id: node.metricId,
      child_id: childId,
      weight: info.weightBeingEdited
    };
    this.apiService.post('/metrics/update_child_weight', payload).subscribe((response) => {
      info.weight = info.weightBeingEdited;
    });
    info.weightEditing = false;
  };

  closeEditingWeightClick = (info) => {
    info.weightEditing = false;
  };

  updateNumBug(numBugs, node): void {
    node.numBugs = numBugs;
  }

  //copy atomic URL to clipboard
  copyAtomicUrl(): string {
    let baseUrl = window.location.protocol +
      '//' + window.location.hostname +
      ':' + window.location.port;
    let url = baseUrl + "/performance/atomic/" + this.currentNode.metricId;
    this.clipboardService.copyFromContent(url);
    let message = 'URL: ' + url + " copied to clipboard";
    this.toolTipMessage = message;
    //alert(message);
    this.copyUrlTooltip.open();
    return message;
  }

}
