import {Component, EventEmitter, Input, OnInit, Output, Renderer2, ViewChild} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";
import {Title} from "@angular/platform-browser";
import {CommonService} from "../services/common/common.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {PerformanceService, SelectMode} from "./performance.service";


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
  jiraIds: any = [];
  showAddJira: boolean = false;
  degrades: any = new Set();
  upgrades: any = new Set();
  failures: any = new Set();
  bugs: any = {};
  positive: boolean = true;
  workInProgress: boolean = false;
  tags: string = null;
  companionCharts: number[] = null;
  chartInfo: any = null;
  pastStatus: any = null;
}

class FlatNode {
  gUid: number;
  node: Node;
  collapsed: boolean;
  hide: boolean;
  indent: number;
  showJiraInfo: boolean = false;
  showGitInfo: boolean = false;
  jiraList: any = {};
  context: any = new Set();
  children: FlatNode[] = [];
  lineage: any = [];
  special: boolean = false;
  showAddLeaf: boolean = false;
  track: boolean = false;
  subscribe: boolean = false;

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
  selector: 'app-performance',
  templateUrl: './performance.component.html',
  styleUrls: ['./performance.component.css']
})

export class PerformanceComponent implements OnInit {
  //used for workspace editing
  @Input() selectMode: SelectMode = SelectMode.ShowMainSite; //allows only to select metrics and not display any charts
  @Input() userProfileEmail: string = null; //the current workspace user email
  @Input() workspaceId: number = null; //current workspace Id
  @Input() interestedMetrics: any = null; //metrics already part of the workspace
  @Input() description: string = null; //workspace description
  @Output() editedWorkspace: EventEmitter<boolean> = new EventEmitter(); //successful submission of metrics to DB
  @Input() metricIds: number[] = null;
  updatedInterestedMetrics: any = [];
  SelectMode = SelectMode;

  numGridColumns: number;
  lastStatusUpdateTime: any;
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
  showScoreInfo: boolean = false;
  miniGridMaxWidth: string;
  miniGridMaxHeight: string;
  status: string = null;
  flatNodesMap: any = {};

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

  static LSF_BASE_URL: string = "http://palladium-jobs.fungible.local:8080/job/";
  static JENKINS_BASE_URL: string = "http://jenkins-sw-master:8080/job/emulation/job/scheduled_emulation/";
  static REGRESSION_BASE_URL: string = "/regression/suite_detail/";

  globalSettings: any = null;
  toolTipMessage: string = null;
  @ViewChild('copyUrlTooltip') copyUrlTooltip;
  chartReady: boolean = false;
  lastScore: number;
  penultimateScore: number;
  deviation: any;

  upgradeFlatNode: any = {};
  degradeFlatNode: any = {};
  tagsForId = {
    493: ["PCIe"]
  };

  jiraList: any = {};
  showBugPanel: boolean = false;

  gotoQueryBaseUrl: string = "/performance?goto=";
  queryPath: string = null;  // includes gotoQueryBaseUrl and a query
  queryExists: boolean = false; //decides whether to just expand the node or to do both expand and show charts

  slashReplacement: string = "_fsl"; //forward slash

  rootNode: FlatNode = null;
  lastF1Lineage: string = null;
  lastS1Lineage: string = null;
  f1Dag: any = null;
  s1Dag: any = null;

  buildInfo: any = null;
  showF1Dag: boolean = true;
  showS1Dag: boolean = false;
  initialize: boolean = true;

  constructor(
    private apiService: ApiService,
    private loggerService: LoggerService,
    private title: Title,
    private commonService: CommonService,
    private activatedRoute: ActivatedRoute,
    private router: Router,
    private renderer: Renderer2,
    private service: PerformanceService
  ) {
  }

  ngOnInit() {
    console.log("Component Init");
    if (this.selectMode == SelectMode.ShowMainSite) {
      this.title.setTitle('Performance');
    }
    this.status = "Loading";
    this.numGridColumns = 2;
    this.miniGridMaxWidth = '50%';
    this.miniGridMaxHeight = '50%';
    this.fetchGlobalSettings();
    if (window.screen.width >= 1690) {
      this.numGridColumns = 4;
      this.miniGridMaxWidth = '25%';
      this.miniGridMaxHeight = '25%';
    }
    this.buildInfo = null;
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.service.fetchBuildInfo();
      })).subscribe(response => {
      this.buildInfo = response;
      console.log("fetched buildInfo");
    }, error => {
      this.loggerService.error("Unable to fetch buildInfo");
    });
    if (this.selectMode == SelectMode.ShowMainSite) {
      this.processUrl();
    } else {
      this.fetchDag();
    }
  }

  getDefaultQueryPath(flatNode) {
    return this.gotoQueryBaseUrl + flatNode.node.chartName;
  }

  getQueryPath() {
    return this.activatedRoute.queryParams.pipe(switchMap(params => {
      let queryPath = null;
      if (params.hasOwnProperty('goto')) {
        queryPath = params['goto'];
        // console.log("QueryPath: " + this.queryPath);
        if (this.queryPath !== (this.gotoQueryBaseUrl + queryPath)) {
          this.queryPath = this.gotoQueryBaseUrl + queryPath;
        }
        return of(queryPath);
      }
      else {
        return of(null);
      }

    }))
  }

  getRoutablePathByGuid(guid) {
    let flatNode = this.getFlatNodeByGuid(guid);
    return this.gotoQueryBaseUrl + this.lineageToPath(flatNode.lineage[0]);

  }

  getGuid(): number {
    this.lastGuid++;
    return this.lastGuid;
  }

  getJiraListLength(jiraList): number {
    return Object.keys(jiraList).length;
  }

  gitIdentify(): void {
    this.gitDiagnose = !this.gitDiagnose
  }

  fetchGlobalSettings(): void {
    this.apiService.get("/metrics/global_settings").subscribe(response => {
      this.globalSettings = response.data;
    }, error => {
      this.loggerService.error("fetchGlobalSettings");
    });
  }

  setDefaultFlatNodes(): void {
    this.flatNodes = [];
    this.guIdFlatNodeMap = {};
    this.flatNodesMap = {};
    this.upgradeFlatNode = {};
    this.degradeFlatNode = {};
  }

  setDefaultsForDag(): void {
    this.queryExists = false;
    this.queryPath = null;
    this.showBugPanel = false;
    this.chartReady = false;
    this.currentNode = null;
    this.currentFlatNode = null;
  }

  fetchS1Dag(): void {
    this.showS1Dag = true;
    this.showF1Dag = false;
    this.setDefaultFlatNodes();
    this.fetchDag();
  }

  openS1Dag(): void {
    this.lastF1Lineage = this.queryPath;
    this.setDefaultsForDag();
    if (this.lastS1Lineage) {
      this.initialize = true;
      this.router.navigateByUrl(this.lastS1Lineage);
    } else {
      this.fetchS1Dag();
    }
  }

  fetchF1Dag(): void {
    this.showF1Dag = true;
    this.showS1Dag = false;
    this.setDefaultFlatNodes();
    this.fetchDag();
  }

  openF1Dag(): void {
    this.lastS1Lineage = this.queryPath;
    this.setDefaultsForDag();
    if (this.lastF1Lineage) {
      this.initialize = true;
      this.router.navigateByUrl(this.lastF1Lineage);
    } else {
      this.fetchF1Dag();
    }

  }

   setDag(): any {
    let url = "/metrics/dag";
    let fetchIt = true;
    if (this.selectMode == SelectMode.ShowEditWorkspace) {
      url = "/metrics/dag" + "?root_metric_ids=101,591";
    } else {
      if (this.showF1Dag) {
        url += "?root_metric_ids=101";
      }
      if (this.showS1Dag) {
        url += "?root_metric_ids=591";
      }
      if (this.metricIds) {
        url = "/metrics/dag" + "?root_metric_ids=" + String(this.metricIds) + "&workspace=true";
      }
      if ((this.showF1Dag && this.f1Dag) || (this.showS1Dag && this.s1Dag)) {
        fetchIt = false;
      }
    }
    if (fetchIt) {
     return this.apiService.get(url).pipe(switchMap(response => {
       if (this.showF1Dag) {
         this.f1Dag = response.data;
       } else {
         this.s1Dag = response.data;
       }
        return of(response.data);
    }));
    } else {
      if (this.showF1Dag) {
        return of(this.f1Dag);
      } else {
        return of(this.s1Dag);
      }
    }
  }

  fetchDag(): void {
    this.status = "Fetching DAG";
    new Observable(observer => {
        observer.next(true);
        observer.complete();
        return () => {
        }
      }).pipe(
        switchMap(response => {
          return this.setDag();
        })).subscribe(response => {
        this.dag = response;
        let lineage = [];
      for (let dag of this.dag) {
        this.walkDag(dag, lineage);
      }
      if (this.selectMode == SelectMode.ShowMainSite) {
        this.updateUpDownSincePrevious(true);
        this.updateUpDownSincePrevious(false);
      }
      //total container should always appear
      if (this.selectMode == SelectMode.ShowMainSite) {
        this.rootNode = this.flatNodes[0];
        this.rootNode.hide = false;
        this.expandUrl();
      }
      if (this.selectMode == SelectMode.ShowEditWorkspace && this.interestedMetrics) {
        this.flatNodes[0].hide = false;
        for (let flatNode of this.flatNodes) {
          for (let metric of this.interestedMetrics) {
            if (flatNode.node.metricId === metric.metric_id) {
              flatNode.showAddLeaf = true;
              flatNode.track = true;
              flatNode.subscribe = metric.subscribe;
            }
          }

        }
      }
      this.status = null;
      }, error => {
        this.loggerService.error("Unable to fetch Dag");
      });
    // let url = "/metrics/dag";
    // if (this.selectMode == SelectMode.ShowEditWorkspace) {
    //   url = "/metrics/dag" + "?root_metric_ids=101,591";
    // } else {
    //   if (this.showF1Dag) {
    //     url += "?root_metric_ids=101";
    //   }
    //   if (this.showS1Dag) {
    //     url += "?root_metric_ids=591";
    //   }
    //   if (this.metricIds) {
    //     url = "/metrics/dag" + "?root_metric_ids=" + String(this.metricIds) + "&workspace=true";
    //   }
    // }
    // // Fetch the DAG
    // this.apiService.get(url).subscribe(response => {
    //   this.dag = response.data;
    //   let lineage = [];
    //   for (let dag of this.dag) {
    //     this.walkDag(dag, lineage);
    //   }
    //   if (this.selectMode == SelectMode.ShowMainSite) {
    //     this.updateUpDownSincePrevious(true);
    //     this.updateUpDownSincePrevious(false);
    //   }
    //   //total container should always appear
    //   if (this.selectMode == SelectMode.ShowMainSite) {
    //     this.rootNode = this.flatNodes[0];
    //     this.rootNode.hide = false;
    //     this.expandUrl();
    //   }
    //   if (this.selectMode == SelectMode.ShowEditWorkspace && this.interestedMetrics) {
    //     this.flatNodes[0].hide = false;
    //     for (let flatNode of this.flatNodes) {
    //       for (let metric of this.interestedMetrics) {
    //         if (flatNode.node.metricId === metric.metric_id) {
    //           flatNode.showAddLeaf = true;
    //           flatNode.track = true;
    //           flatNode.subscribe = metric.subscribe;
    //         }
    //       }
    //
    //     }
    //   }
    //   this.status = null;
    //
    // }, error => {
    //   this.loggerService.error("fetchDag");
    // });
  }

  processUrl(): void {
    this.getQueryPath().subscribe(queryPath => {
      if (!queryPath) {
        this.queryExists = false;
        if (this.initialize) {
          this.fetchDag();
          this.initialize = false;
        } else {
          this.expandUrl();
        }
      } else {
        this.queryExists = true;
        if (this.initialize) {
          if (queryPath.startsWith("F1")) {
            this.fetchF1Dag();
          }
          if (queryPath.startsWith("S1")) {
            this.fetchS1Dag();
          }
          this.initialize = false;
        } else {
          this.expandUrl();
        }

      }
    });
  }

  expandUrl(): void {
    if (!this.queryPath) {
      this.queryPath = this.getDefaultQueryPath(this.rootNode);
    }
    let pathGuid = this.pathToGuid(this.queryPath);
    let targetFlatNode = this.guIdFlatNodeMap[pathGuid];
    this.expandNode(targetFlatNode);

    if (this.queryExists) {
      if (targetFlatNode.node.leaf) {
        this.showAtomicMetric(targetFlatNode);
      } else {
        this.showNonAtomicMetric(targetFlatNode);
      }
    }
  }

  updateUpDownSincePrevious(upgrade: boolean): void {
    let statusNode = null;
    let statusFlatNode = null;
    let node = new Node();
    if (upgrade) {
      node.chartName = "Up Since Previous";
      node.numLeaves = Object.keys(this.upgradeFlatNode).length;
      statusFlatNode = this.upgradeFlatNode;
    } else {
      node.chartName = "Down Since Previous";
      node.numLeaves = Object.keys(this.degradeFlatNode).length;
      statusFlatNode = this.degradeFlatNode;
    }
    statusNode = this.getNewFlatNode(node, 0);
    statusNode.hide = false;
    statusNode.special = true;
    this.flatNodes.push(statusNode);
    this.flatNodesMap[statusNode.gUid] = statusNode;
    for (let child in statusFlatNode) {
      let statusChild = statusFlatNode[child];
      statusChild.indent = 1;
      statusNode.addChild(statusChild);
      this.flatNodes.push(statusChild);
      this.flatNodesMap[statusChild.gUid] = statusChild;
    }
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
    node.jiraIds = dagEntry.jira_ids;
    node.showAddJira = false;
    node.positive = dagEntry.positive;
    node.workInProgress = dagEntry.work_in_progress;
    node.companionCharts = dagEntry.companion_charts;
    if (metricId in this.tagsForId) {
      node.tags = this.tagsForId[metricId];
    }

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

  getNameForParent(parent): string {
    for (let key in parent) {
      return parent[key];
    }

  }

  lineageToPath(lineage) {
    let s = "";
    lineage.forEach(part => {
      let name = part.chartName.replace("/", this.slashReplacement);
      s += "/" + encodeURIComponent(name);
    });
    s = s.slice(1, s.length); // Remove leading slash
    return s;
  }

  getQueuryPathByMetricId(metricId) {

  }

  expandFromLineage(parent): void {
    this.chartReady = false;
    let flatNode = this.flatNodesMap[parent.guid];
    let node = flatNode.node;
    this.expandNode(flatNode);
    if (node.metricModelName === 'MetricContainer') {
      this.showNonAtomicMetric(flatNode);
    } else {
      this.showAtomicMetric(flatNode);
    }
    this.chartReady = true;
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
    // console.log("Prepare Grid nodes");
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
        this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(last actual value/reference value) * 100&nbsp)/n";
      } else {
        this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(reference value/last actual value) * 100&nbsp)/n";
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
    newFlatNode.showGitInfo = false;
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
    if (newNode.chartName === "S1" || newNode.chartName === "All metrics" || newNode.chartName === "F1") {
      thisFlatNode.hide = false;
      lineage = [];
    }
    if (this.metricIds && this.metricIds.includes(newNode.metricId)) {
      thisFlatNode.hide = false;
      lineage = [];
    }
    this.guIdFlatNodeMap[thisFlatNode.gUid] = thisFlatNode;
    this.flatNodes.push(thisFlatNode);
    this.flatNodesMap[thisFlatNode.gUid] = thisFlatNode;
    //this.loggerService.log('Node:' + nodeInfo.chart_name);
    let parentsGuid = {};
    parentsGuid["guid"] = thisFlatNode.gUid;
    parentsGuid["chartName"] = newNode.chartName;
    lineage.push(parentsGuid);
    thisFlatNode.lineage = [lineage.slice()];
    if (!nodeInfo.leaf) {
      let children = nodeInfo.children;

      children.forEach((cId) => {
        //let childEntry: {[childId: number]: object} = {cId: nodeInfo.children_info[Number(childId)]};
        let childEntry = nodeInfo.children_info[Number(cId)];
        let childFlatNode = this.walkDag(childEntry, lineage.slice(), indent + 1);
        this.addUpDownStatusNumbers(childFlatNode, thisFlatNode);

        thisFlatNode.addChild(childFlatNode);
      });
    } else {
      this.addUpgradeDegradeNodes(thisFlatNode, dagEntry);
    }
    return thisFlatNode;
  }

  addUpDownStatusNumbers(childFlatNode, thisFlatNode): void {
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
      Object.keys(childNode.bugs).forEach((function (key) {
        thisFlatNode.node.bugs[key] = childNode.bugs[key];
      }));
    }
    if (Object.keys(thisFlatNode.node.bugs).length != 0) {
      Object.keys(thisFlatNode.node.bugs).forEach(k => {
        let bugObj = thisFlatNode.node.bugs[k];
        let context = "";
        if (bugObj.context) {
          for (let el of bugObj.context) {
            for (let child of el) {
              let path = this.getRoutablePathByGuid(child.guid);
              context += `<a href="${path}"> ${child.chartName}</a>`;
              context += "->";
            }
          }

          context = context.replace(/->$/, "<br>");

        }
        if (bugObj.jiraIds) {
          for (let id of bugObj.jiraIds) {
            if (thisFlatNode.jiraList[id]) {
              thisFlatNode.jiraList[id].context += context;

            } else {
              thisFlatNode.jiraList[id] = {context: context}
            }
          }
        }


      });
    }
  }

  getFlatNodeByGuid(guId) {
    let result = null;
    if (this.guIdFlatNodeMap.hasOwnProperty(guId)) {
      result = this.guIdFlatNodeMap[guId];
    }
    return result;
  }

  addUpgradeDegradeNodes(thisFlatNode, dagEntry): void {
    let leafNode = thisFlatNode.node;
    if (leafNode.trend > 0) {
      leafNode.upgrades.add(leafNode.metricId);
      this.addLineagesForUpgradesDegrades(true, leafNode, dagEntry, thisFlatNode);
    } else if (leafNode.trend < 0) {
      leafNode.degrades.add(leafNode.metricId);
      this.addLineagesForUpgradesDegrades(false, leafNode, dagEntry, thisFlatNode);
    }
    if (leafNode.lastNumBuildFailed == 1) {
      leafNode.failures.add(leafNode.metricId);
    }
    if (leafNode.numBugs > 0) {
      let value = {};
      value["jiraIds"] = leafNode.jiraIds;
      value["context"] = thisFlatNode.lineage;
      leafNode.bugs[leafNode.metricId] = value;
    }
  }

  addLineagesForUpgradesDegrades(upgrade: boolean, leafNode: Node, dagEntry: any, thisFlatNode: any): void {
    let newLeafNode = this.getNodeFromEntry(leafNode.metricId, dagEntry);
    let flatNode = this.getNewFlatNode(newLeafNode, 1);
    let statusNode = null;
    for (let p of thisFlatNode.lineage) {
      flatNode.lineage.push(p);
    }
    if (upgrade) {
      statusNode = this.upgradeFlatNode;
    } else {
      statusNode = this.degradeFlatNode;
    }
    if (statusNode[newLeafNode.metricId]) {
      let tempNode = statusNode[newLeafNode.metricId];
      for (let p of thisFlatNode.lineage) {
        tempNode.lineage.push(p);
      }
    } else {
      statusNode[newLeafNode.metricId] = flatNode;
    }
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

  getLastStatusUpdateTime() {
    this.apiService.get('/common/time_keeper/' + "last_status_update").subscribe((data) => {
      this.lastStatusUpdateTime = data;
    }, error => {

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

  getStatusHtml = (flatNode) => {
    let s = "";
    if (flatNode.node.degrades.size != 0) {
      s += "<span style='color: red'><i class='fa fa-arrow-down aspect-trend-icon fa-icon-red'>:</i></span>" + flatNode.node.degrades.size + "";
    }
    if (flatNode.node.failures.size != 0) {
      if (flatNode.node.degrades.size != 0) {
        s += "&nbsp";
      }
      s += "<span style='color: red'><i class='fa fa-times fa-icon-red'>:</i></span>" + "<span style='color: black'>" + flatNode.node.failures.size + "</span>";
    }
    return s;
  };

  openBugPanel(flatNode): void {
    this.mode = Mode.ShowingBugPanel;
    this.chartReady = false;
    this.showBugPanel = !this.showBugPanel;
    this.jiraList = flatNode.jiraList;
  }

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
        this.currentRegressionUrl = PerformanceComponent.REGRESSION_BASE_URL + result.last_suite_execution_id;
      }
      if (result.last_jenkins_job_id && result.last_jenkins_job_id !== -1) {
        this.currentJenkinsUrl = PerformanceComponent.JENKINS_BASE_URL + result.last_jenkins_job_id;
      }
      if (result.last_lsf_job_id && result.last_lsf_job_id !== -1) {
        this.currentLsfUrl = PerformanceComponent.LSF_BASE_URL + result.last_lsf_job_id;
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
        this.failedRegressionUrl = PerformanceComponent.REGRESSION_BASE_URL + result.failed_suite_execution_id;
      }
      if (result.failed_jenkins_job_id && result.failed_jenkins_job_id !== -1) {
        this.failedJenkinsUrl = PerformanceComponent.JENKINS_BASE_URL + result.failed_jenkins_job_id;
      }
      if (result.failed_lsf_job_id && result.failed_lsf_job_id !== -1) {
        this.failedLsfUrl = PerformanceComponent.LSF_BASE_URL + result.failed_lsf_job_id;
      }
      if (result.failed_git_commit && result.failed_git_commit !== "") {
        this.failedGitCommit = result.failed_git_commit;
      }
      if (result.passed_date_time) {
        this.passedDateTime = result.passed_date_time;
      }
      if (result.passed_suite_execution_id && result.passed_suite_execution_id !== -1) {
        this.passedRegressionUrl = PerformanceComponent.REGRESSION_BASE_URL + result.passed_suite_execution_id;
      }
      if (result.passed_jenkins_job_id && result.passed_jenkins_job_id !== -1) {
        this.passedJenkinsUrl = PerformanceComponent.JENKINS_BASE_URL + result.passed_jenkins_job_id;
      }
      if (result.passed_lsf_job_id && result.passed_lsf_job_id !== -1) {
        this.passedLsfUrl = PerformanceComponent.LSF_BASE_URL + result.passed_lsf_job_id;
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

  fetchChartInfo(flatNode) {
    if (flatNode.node.leaf && (!flatNode.node.chartInfo || !flatNode.node.pastStatus)) {
      this.service.chartInfo(flatNode.node.metricId).subscribe((response) => {
        flatNode.node.chartInfo = response;
        this.service.pastStatus(flatNode.node.metricId).subscribe((response) => {
          flatNode.node.pastStatus = response;
        }, error => {
          console.error("Unable to fetch past status"); //TODO
        })

      }, error => {
        console.error("Unable to fetch chartInfo");
      })
    }
  }

  showAtomicMetric = (flatNode) => {
    if (this.selectMode == SelectMode.ShowMainSite || this.selectMode == SelectMode.ShowViewWorkspace) {
      this.chartReady = false;
      if (this.currentNode && this.currentNode.showAddJira) {
        this.currentNode.showAddJira = false;
      }
      if (this.currentFlatNode && this.currentFlatNode.showJiraInfo) {
        this.currentFlatNode.showJiraInfo = false;
      }
      if (this.currentFlatNode && this.currentFlatNode.showGitInfo) {
        this.currentFlatNode.showGitInfo = false;
      }
      this.showBugPanel = false;
      this.currentNode = flatNode.node;
      this.currentFlatNode = flatNode;
      this.currentNode.showAddJira = true;
      this.mode = Mode.ShowingAtomicMetric;
      this.expandNode(flatNode);
      this.commonService.scrollTo("chart-info");
      this.chartReady = true;
      // if (this.selectMode == SelectMode.ShowMainSite) {
      //   this.navigateByQuery(flatNode);
      // }
      this.fetchChartInfo(flatNode);
    } else if (this.selectMode == SelectMode.ShowEditWorkspace) {
      flatNode.showAddLeaf = true;
      this.currentNode = flatNode.node;
      this.currentFlatNode = flatNode;
    } else {
      this.currentNode = flatNode.node;
      this.currentFlatNode = flatNode;
      this.mode = Mode.ShowingAtomicMetric;
      this.expandNode(flatNode);
      this.commonService.scrollTo("chart-info");
      this.chartReady = true;
      this.fetchChartInfo(flatNode);
    }
  };

  showNonAtomicMetric = (flatNode) => {
    if (this.selectMode == SelectMode.ShowMainSite || this.selectMode == SelectMode.ShowViewWorkspace) {
      if (flatNode.node.metricModelName && flatNode.node.chartName !== "All metrics") {
        this.chartReady = false;
        if (this.currentNode && this.currentNode.showAddJira) {
          this.currentNode.showAddJira = false;
        }
        if (this.currentFlatNode && this.currentFlatNode.showJiraInfo) {
          this.currentFlatNode.showJiraInfo = false;
        }
        if (this.currentFlatNode && this.currentFlatNode.showGitInfo) {
          this.currentFlatNode.showGitInfo = false;
        }
        this.showBugPanel = false;
        this.currentNode = flatNode.node;
        this.currentNode.showAddJira = true;
        if (this.currentNode && this.currentNode.companionCharts) {
          this.currentNode.companionCharts = [...this.currentNode.companionCharts];
        }
        this.currentFlatNode = flatNode;
        this.mode = Mode.ShowingNonAtomicMetric;
        this.expandNode(flatNode);
        if (this.selectMode == SelectMode.ShowMainSite) {
          this.prepareGridNodes(flatNode.node);
          this.commonService.scrollTo("chart-info");
        }
        this.chartReady = true;
      } else {
        this.chartReady = false;
        this.expandNode(flatNode);
        this.chartReady = true;
      }
      // if (!flatNode.special && this.selectMode == SelectMode.ShowMainSite) {
      //   this.navigateByQuery(flatNode);
      // }
      this.fetchChartInfo(flatNode);
    } else {
      this.expandNode(flatNode);
      this.currentNode = flatNode.node;
      this.currentFlatNode = flatNode;
      if (this.selectMode == SelectMode.ShowEditWorkspace) {
        this.currentFlatNode.showAddLeaf = true;
      }
    }
  };

  getStringLineage(lineages): string {
    let result = "";
    for (let lineage of lineages[0]) {
      result += lineage.chartName + "/";
    }
    return result.slice(0, -1);//to remove the slash after the last chart name
  }

  submitInterestedMetrics(): void {
    let flatNodes = this.getInterestedNodes();
    let metricDetails = {};
    this.updatedInterestedMetrics = [];
    for (let flatNode of flatNodes) {
      if (!(flatNode.node.metricId in metricDetails)) {
        let lineage = this.getStringLineage(flatNode.lineage);
        metricDetails[flatNode.node.metricId] = {
          "metric_id": flatNode.node.metricId, "subscribe": flatNode.subscribe, "track": flatNode.track,
          "lineage": lineage, "chart_name": flatNode.node.chartName, "category": 'General', "comments": ''
        };
      }
    }
    Object.keys(metricDetails).forEach(id => {
      this.updatedInterestedMetrics.push(metricDetails[id]);
    });

    let payload = {};
    payload["email"] = this.userProfileEmail;
    payload["workspace_id"] = this.workspaceId;
    payload["interested_metrics"] = this.updatedInterestedMetrics;
    this.apiService.post("/api/v1/performance/workspaces/" + this.workspaceId + "/interested_metrics", payload).subscribe(response => {
      console.log("submitted successfully");
      this.editedWorkspace.emit(true);
    }, error => {
      this.loggerService.error("Unable to submit interested metrics");
    });
  }

  cancelInterestedMetrics(): void {
    this.editedWorkspace.emit(false);
  }

  getInterestedNodes = () => {
    return this.flatNodes.filter(flatNode => {
      return flatNode.track || flatNode.subscribe;
    });
  };

  removeFromInterestedList(metricId): void {
    for (let flatNode of this.flatNodes) {
      if (flatNode.node.metricId == metricId) {
        flatNode.track = false;
        flatNode.subscribe = false;
        flatNode.showAddLeaf = false;
      }
    }
  }

  onChangeSubscribeTo(subscribed, metricId): void {
    for (let flatNode of this.flatNodes) {
      if (flatNode.node.metricId == metricId) {
        flatNode.subscribe = subscribed;
      }
    }
  }

  onChangeTrack(tracking, metricId): void {
    for (let flatNode of this.flatNodes) {
      if (flatNode.node.metricId == metricId) {
        flatNode.track = tracking;
      }
    }
  }

  navigateByQuery(flatNode) {
    if (this.selectMode == SelectMode.ShowMainSite) {
      let path = this.lineageToPath(flatNode.lineage[0]);
      let queryPath = this.gotoQueryBaseUrl + path;
      this.router.navigateByUrl(queryPath);
    } else {
      if (!flatNode.node.leaf) {
        this.showNonAtomicMetric(flatNode);
      } else {
        this.showAtomicMetric(flatNode);
      }
    }
  }

  pathToGuid(path) {
    let result = null;
    try {
      path = path.replace(this.gotoQueryBaseUrl, "");
      let parts = path.split("/");
      result = this._doPathToGuid(this.rootNode, parts);
      // console.log("Path: " + path + " : guid: " + result + " c: " + this.getFlatNodeByGuid(result).node.chartName);

    } catch (e) {

    }
    return result;
  }

  _doPathToGuid(flatNode, remainingParts) {
    let result = null;
    if (remainingParts.length > 0) {
      let remainingPart = remainingParts[0].replace(this.slashReplacement, "/");
      if (remainingPart === "Total") {
        remainingPart = "F1";
      }
      if (flatNode.node.chartName === decodeURIComponent(remainingPart)) {
        // match found
        if (remainingParts.length > 1) {
          remainingParts = remainingParts.slice(1, remainingParts.length); // there are more segments to parse
          let remainingPart = remainingParts[0].replace(this.slashReplacement, "/");
          for (let index = 0; index < flatNode.children.length; index++) {
            let childFlatNode = flatNode.children[index];
            if (decodeURIComponent(remainingPart) === childFlatNode.node.chartName) {
              return this._doPathToGuid(childFlatNode, remainingParts);
            }
          }
        } else {
          result = flatNode.gUid;
        }
      }
    }
    return result;
  }


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

  closeLeafPanel(value, flatNode): void {
    if (value) {
      flatNode.showJiraInfo = false;
    }
  }

  closeSummaryPanel(value): void {
    if (value) {
      this.showBugPanel = false;
    }
  }

  static _tooltipInfoElementHelper(self, text, baseUrl, jobId) {
    let urlElement = self.renderer.createElement('a');
    let url = baseUrl + jobId;
    self.renderer.setProperty(urlElement, "href", url);
    self.renderer.setProperty(urlElement, "target", "_blank");
    let textElement = self.renderer.createText(text);
    self.renderer.appendChild(urlElement, textElement);
    return urlElement;
  }

  static _tooltipInfoHelper(self, header, headerValue, lsfJobId, jenkinsJobId, regressionJobId) {
    let divElement = self.renderer.createElement('div');
    let headerElement = self.renderer.createElement('b');
    self.renderer.appendChild(headerElement, self.renderer.createText(header));
    if (headerValue) {
      self.renderer.appendChild(headerElement, self.renderer.createText(headerValue));
    }

    let lsfElement = PerformanceComponent._tooltipInfoElementHelper(self, "LSF log", PerformanceComponent.LSF_BASE_URL, lsfJobId);
    let jenkinsElement = PerformanceComponent._tooltipInfoElementHelper(self, "Jenkins log", PerformanceComponent.JENKINS_BASE_URL, jenkinsJobId);
    let regressionElement = PerformanceComponent._tooltipInfoElementHelper(self, "Regression log", PerformanceComponent.REGRESSION_BASE_URL, regressionJobId);

    let elements = [headerElement, lsfElement, jenkinsElement, regressionElement];
    for (let element of elements) {
      let br = self.renderer.createElement('br');
      self.renderer.appendChild(element, br);
      self.renderer.appendChild(divElement, element);
    }
    return divElement;
  }

  tooltipCallback(self, flatNode) {
    let content = this.renderer.createElement("span");
    if (!flatNode.node.chartInfo || !flatNode.node.pastStatus) {
      const text = this.renderer.createText("Data not yet available. Try again in 10 seconds");
      this.renderer.appendChild(content, text);
    } else {

      let passedElement = PerformanceComponent._tooltipInfoHelper(this, "Last passed:",
        this.commonService.getPrettyLocalizeTime(flatNode.node.pastStatus.passedDateTime),
        flatNode.node.pastStatus.passedLsfJobId,
        flatNode.node.pastStatus.passedJenkinsJobId,
        flatNode.node.pastStatus.passedSuiteExecutionId);
      this.renderer.appendChild(content, passedElement);

      let currentFailedElement = PerformanceComponent._tooltipInfoHelper(this, "Current failure:",
        "",
        flatNode.node.chartInfo.lastLsfJobId,
        flatNode.node.chartInfo.lastJenkinsJobId,
        flatNode.node.chartInfo.lastSuiteExecutionId);
      this.renderer.appendChild(content, currentFailedElement);

      let firstFailedElement = PerformanceComponent._tooltipInfoHelper(this, "First failure:",
        this.commonService.getPrettyLocalizeTime(flatNode.node.pastStatus.failedDateTime),
        flatNode.node.chartInfo.failedLsfJobId,
        flatNode.node.chartInfo.failedJenkinsJobId,
        flatNode.node.chartInfo.failedSuiteExecutionId);
      this.renderer.appendChild(content, firstFailedElement);


    }
    return content;
  }


}
