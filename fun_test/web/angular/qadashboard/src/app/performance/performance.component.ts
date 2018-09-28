import {Component, OnInit} from '@angular/core';
import {Location} from '@angular/common';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";



class Node {
  metricId: number;
  leaf: boolean;
  chartName: string;
  metricModelName: string;
  numChildrenFailed: number;
  numChildrenDegrades: number;
  lastNumBuildFailed: number;
  numLeaves: number
}

class FlatNode {
  gUid: number;
  node: Node;
  collapsed: boolean;
  hide: boolean;
}

@Component({
  selector: 'app-performance',
  templateUrl: './performance.component.html',
  styleUrls: ['./performance.component.css']
})
export class PerformanceComponent implements OnInit {
  numGridColumns: number;
  lastStatusUpdateTime: any;
  mode: any;
  jenkinsJobIdMap: any;
  metricMap: any;
  cachedNodeInfo: any;
  goodnessTrendValues: any;
  inner: any;
  //data: any;
  dataSets: any;
  childData: any;
  headers: any[];
  data: any[];
  dag: any = null;

  nodeMap: { [metricId: number] : Node } = {};
  lastGuid: number = 0;
  flatNodes: FlatNode[] = [];

  constructor(
    private location: Location,
    private apiService: ApiService,
    private loggerService: LoggerService
  ) {
  }

  ngOnInit() {
    // this.getLastStatusUpdateTime();
    this.numGridColumns = 2;
    this.data = [['hi', 'hello'], ['how', 'are'], ['you', 'its'], ['been', 'a'], ['long', 'time'], ['also', 'when'], ['where', 'how'], ['are', 'we'], ['meeting', 'if'], [1, 2], [3, 4]];
    this.headers = ['Names', 'Numbers'];
    this.fetchDag();
    if (window.screen.width <= 1441) {
      this.numGridColumns = 2;
    }
  }

  getGuid(): number {
    this.lastGuid++;
    return this.lastGuid;
  }

  fetchDag(): void {
    // Fetch the DAG
    let payload: { [i: string]: string} = {metric_model_name: "MetricContainer", chart_name: "Total"};
    this.apiService.post("/metrics/dag", payload).subscribe( response => {
      this.dag = response.data;
      this.walkDag(this.dag);
      let i = 0;
    }, error => {
      this.loggerService.error("fetchDag");
    })
  }

  getNodeFromEntry(metricId: number, dagEntry: any): Node {
    let node = new Node();
    node.metricId = metricId;
    node.chartName = dagEntry.chart_name;
    node.metricModelName = dagEntry.metric_model_name;
    node.numLeaves = dagEntry.num_leaves;
    node.numChildrenDegrades = dagEntry.last_num_degrades;
    node.lastNumBuildFailed = dagEntry.last_num_build_failed;
    return node;
  }


  addNodeToMap(metricId: number, node: Node): void {
    this.nodeMap[metricId] = node;
  }

  getNewFlatNode(node: Node): FlatNode {
    let newFlatNode = new FlatNode();
    newFlatNode.gUid = this.getGuid();
    newFlatNode.node = node;
    newFlatNode.hide = true;
    newFlatNode.collapsed = true;
    return newFlatNode;
  }

  walkDag(dagEntry: object): void {
    this.loggerService.log(dagEntry);
    for (let metricId in dagEntry) {
      let numMetricId: number = Number(metricId); // TODO, why do we need this conversion
      let nodeInfo = dagEntry[numMetricId];
      let newNode = this.getNodeFromEntry(numMetricId, dagEntry[numMetricId]);
      this.addNodeToMap(numMetricId, newNode);

      this.flatNodes.push(this.getNewFlatNode(newNode));
      this.loggerService.log('Node:' + nodeInfo.chart_name);
      if (!nodeInfo.leaf) {
        let children = nodeInfo.children;
        children.forEach((cId) => {
          //let childEntry: {[childId: number]: object} = {cId: nodeInfo.children_info[Number(childId)]};
          let childEntry = {[cId]: nodeInfo.children_info[Number(cId)]};
          this.walkDag(childEntry);
        })
      }
    }
  }

  setValues(pageNumber): void {
    this.data = [['hi', 'hello'], ['how', 'are']];
    this.headers = ['Names', 'Numbers'];
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
counter(i: number) {
    return new Array(i);
  }



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

    //     let dateRange = this.getDateRange();
    //     let fromDate = dateRange[0];
    //     let toDate = dateRange[1];
    //     return this.fetchScores(data.metric_id, fromDate.toISOString(), toDate.toISOString()).then((scoreData) => {
    //         newNode.childrenScoreMap = scoreData["children_score_map"];
    //         this.evaluateScores(newNode, scoreData["scores"]);
    //         newNode.childrenWeights.forEach((info, childId) => {
    //             newNode.children[childId] = {weight: newNode.childrenWeights[childId], editing: false};
    //         });
    //
    //         if (newNode.lastBuildStatus === "PASSED") {
    //             newNode.status = true;
    //         } else {
    //             newNode.status = false;
    //         }
    //
    //         let newNodeChildrenIds = JSON.parse(data.children);
    //         if (newNodeChildrenIds.length > 0) {
    //             newNode.numChildren = newNodeChildrenIds.length;
    //         }
    return newNode;
    //     });
    //
    //
  };

  guid = () => {
    function s4() {
      return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
    }

    return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
  };

  expandNode = (node, all) => {
    node.collapsed = false;
    if (node.hasOwnProperty("numChildren") && (node.numChildren > 0)) {
      let thisNode = node;
      // Fetch children ids

      // return this.fetchMetricInfoById(node).then((data) => {
      //     console.log("Fetching Metrics Info for node:" + node.metricId);
      //     node.hide = false;
      //     let childrenIds = JSON.parse(data.children);
      //     return this._insertNewNode(node, childrenIds, all, node.childrenFetched).then(() => {
      //         console.log("Inserted: " + node.chartName);
      //         node.childrenFetched = true;
      //         return null;
      //     });
      //
      // });

    }
    else {
      return null;
    }
    //node.hide = false;

  };


}

//
//     this.clearNodeInfoCache = () => {
//         this.cachedNodeInfo = {};
//     };
//
//
//
//
//
//
//
//     this.getIndex = (node) => {
//         let index = this.flatNodes.map(function(x) {return x.guid;}).indexOf(node.guid);
//         return index;
//     };
//
//     this.getNode = (guid) => {
//         return this.flatNodes[this.getIndex({guid: guid})];
//     };
//
//     this.expandAllNodes = () => {
//         this.flatNodes.forEach((node) => {
//             this.expandNode(node, true);
//         });
//         this.collapsedAll = false;
//         this.expandedAll = true;
//     };
//
//     this.collapseAllNodes = () => {
//         this.collapseNode(this.flatNodes[0]);
//         this.expandedAll = false;
//         this.collapsedAll = true;
//     };
//
//     this.getDateBound = (dt, lower) => {
//         let newDay = new Date(dt);
//         if (lower) {
//             newDay.setHours(0, 0, 1);
//         } else {
//             newDay.setHours(23, 59, 59);
//         }
//
//         return newDay;
//     };
//
//     function isSameDay(d1, d2) {
//           return d1.getFullYear() === d2.getUTCFullYear() &&
//             d1.getUTCMonth() === d2.getUTCMonth() &&
//             d1.getUTCDate() === d2.getUTCDate();
//     }
//
//     this.getYesterday = (today) => {
//         let yesterday = new Date(today);
//         yesterday = yesterday.setDate(yesterday.getDate() - 1);
//         return yesterday;
//     };
//
//
//     this.getDateRange = () => {
//         let today = new Date();
//         console.log(today);
//         let startMonth = 4 - 1;
//         let startDay = 1;
//         let startMinute = 59;
//         let startHour = 23;
//         let startSecond = 1;
//         let fromDate = new Date(today.getFullYear(), startMonth, startDay, startHour, startMinute, startSecond);
//         fromDate = this.getDateBound(fromDate, true);
//         // console.log(fromDate);
//         // console.log(this.getDateBound(fromDate, true));
//         // console.log(this.getDateBound(fromDate, false));
//
//         let yesterday = this.getYesterday(today);
//         let toDate = new Date(yesterday);
//         toDate = this.getDateBound(toDate, false);
//         //let fromDate = new Date();
//         // fromDate.setDate(toDate.getDate() - 7);
//         // fromDate = this.getDateBound(fromDate, true);
//         return [fromDate, toDate];
//
//     };
//
//
//
//     this.fetchScores = (metricId, fromDate, toDate) => {
//         let payload = {};
//         payload.metric_id = metricId;
//         payload.date_range = [fromDate, toDate];
//         return commonService.apiPost('/metrics/scores', payload).then((data) => {
//             return data;
//         });
//     };
//
//
//     this.getSumChildWeights = (children) => {
//         let sumOfWeights = 0;
//         angular.forEach(children, (info, childId) => {
//             sumOfWeights += info.weight;
//         });
//         return sumOfWeights;
//     };
//
//     this.getScoreTotal = (currentNode) => {
//         let children = currentNode.children;
//         let scoreTotal = 0;
//
//
//         angular.forEach(children, (info, childId) => {
//             scoreTotal += info.weight * currentNode.childrenScoreMap[childId];
//         });
//
//         let lastDate = new Date(this.validDates.slice(-1)[0] * 1000);
//         let lastDateLower = this.getDateBound(lastDate, true);
//         let lastDateUpper = this.getDateBound(lastDate, false);
//
//
//
//
//         return scoreTotal;
//     };
//
//     this.evaluateScores = (node, scores) => {
//
//         let keys = Object.keys(scores);
//         let sortedKeys = keys.sort();
//         if (node.chartName === "Total") {
//             this.validDates = sortedKeys;
//         }
//
//         if (Object.keys(scores).length) {
//
//             let mostRecentDateTimestamp = sortedKeys.slice(-1)[0];
//             let mostRecentDate = new Date(mostRecentDateTimestamp * 1000);
//             console.log(mostRecentDate);
//             console.log(scores[mostRecentDateTimestamp].score);
//             /*
//             let dateRange = this.getDateRange();
//             let fromDate = dateRange[0].getTime()/1000;
//             let toDate = dateRange[1].getTime()/1000;
//             let lastEntry = scores[toDate].score;*/
//         }
//         let goodnessValues = [];
//         sortedKeys.forEach((key) => {
//             goodnessValues.push(scores[key].score);
//         });
//
//         // console.log("Goodness values: " + goodnessValues);
//
//         node.goodnessValues = goodnessValues;
//         try {
//                 node.goodness = Number(goodnessValues[goodnessValues.length - 1].toFixed(1));
//         } catch (e) {
//
//         }
//
//         node.childrenGoodnessMap = {};
//         node.trend = "flat";
//         if (goodnessValues.length > 1) {
//             let penultimateGoodness = Number(goodnessValues[goodnessValues.length - 2].toFixed(1));
//             if (penultimateGoodness > node.goodness) {
//                 node.trend = "down";
//             } else if (penultimateGoodness < node.goodness) {
//                 node.trend = "up";
//             }
//             if (Number(goodnessValues[goodnessValues.length - 1].toFixed(1)) === 0) {
//                 node.trend = "down";
//             }
//         }
//         console.log("Node: " + node.chartName + " Goodness: " + node.goodness);
//     };
//
//     this.evaluateGoodness = (node, goodness_values, children_goodness_map) => {
//         if (goodness_values.length) {
//             try {
//                 node.goodness = Number(goodness_values[goodness_values.length - 1].toFixed(1));
//             } catch (e) {
//             }
//             node.goodnessValues = goodness_values;
//             node.childrenGoodnessMap = children_goodness_map;
//             node.trend = "flat";
//             let penultimateGoodness = Number(goodness_values[goodness_values.length - 2].toFixed(1));
//             if (penultimateGoodness > node.goodness) {
//                 node.trend = "down";
//             } else if (penultimateGoodness < node.goodness) {
//                 node.trend = "up";
//             }
//             if (Number(goodness_values[goodness_values.length - 1].toFixed(1)) === 0) {
//                 node.trend = "down";
//             }
//         }
//     };
//
//     this.getLastElement = (array) => {
//         let result = null;
//         if (array.length) {
//             result = array[array.length - 1];
//         }
//         return result;
//     };
//
//     this.setCurrentChart = (node) => {
//         this.mode = "showingAtomicMetric";
//         this.currentChartName = node.chartName;
//         this.currentMetricModelName = node.metricModelName;
//         this.currentNode = node;
//     };
//
//     this.showNodeInfoClick = (node) => {
//         if(this.currentMetricModelName === 'MetricContainer') {
//             this.showingContainerNodeInfo = !this.showingContainerNodeInfo;
//         }
//         else {
//             this.showingNodeInfo = !this.showingNodeInfo;
//             this.currentNodeInfo = null;
//             if (node.positive) {
//                 this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(last actual value/expected value) * 100&nbsp)/n";
//             } else {
//                 this.currentNodeInfo = "(&nbsp&#8721; <sub>i = 1 to n </sub>(expected value/last actual value) * 100&nbsp)/n";
//             }
//             this.currentNodeInfo += "&nbsp, where n is the number of data-sets";
//         }
//     };
//
//
//
//
//     this.getChildWeight = (node, childMetricId) => {
//         if (node.hasOwnProperty("childrenWeights")) {
//             return node.childrenWeights[childMetricId];
//         } else {
//             return 0;
//         }
//     };
//
//     this.editDescriptionClick = () => {
//         this.editingDescription = true;
//     };
//
//
//     this.closeEditingDescriptionClick = () => {
//         this.editingDescription = false;
//     };
//
//     this.openAtomicTab = () => {
//         let url = "/metrics/atomic/" + this.currentChartName + "/" + this.currentMetricModelName;
//         $window.open(url, '_blank');
//     };
//
//     this.submitDescription = (node) => {
//         let payload = {};
//         payload["metric_model_name"] = node.metricModelName;
//         payload["chart_name"] = node.chartName;
//         payload["description"] = this.inner.nonAtomicMetricInfo;
//
//         // TODO: Refresh cache
//         commonService.apiPost('/metrics/update_chart', payload, "EditDescription: Submit").then((data) => {
//             if (data) {
//                 alert("Submitted");
//             } else {
//                 alert("Submission failed. Please check alerts");
//             }
//         });
//         this.editingDescription = false;
//
//     };
//
//     this.tooltipFormatter = (x, y) => {
//         let softwareDate = "Unknown";
//         let hardwareVersion = "Unknown";
//         let sdkBranch = "Unknown";
//         let gitCommit = "Unknown";
//         let r = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/g;
//         let match = r.exec(x);
//         let key = "";
//         if (match) {
//             key = match[1];
//         }
//         let s = "";
//
//         if (key in this.buildInfo) {
//             softwareDate = this.buildInfo[key]["software_date"];
//             hardwareVersion = this.buildInfo[key]["hardware_version"];
//             sdkBranch = this.buildInfo[key]["fun_sdk_branch"]
//             s = "<b>SDK branch:</b> " + sdkBranch + "<br>";
//             s += "<b>Software date:</b> " + softwareDate + "<br>";
//             s += "<b>Hardware version:</b> " + hardwareVersion + "<br>";
//             s += "<b>Git commit:</b> " + this.buildInfo[key]["git_commit"].replace("https://github.com/fungible-inc/FunOS/commit/", "")  + "<br>";
//             s += "<b>Value:</b> " + y + "<br>";
//         } else {
//             s += "<b>Value:</b> " + y + "<br>";
//         }
//
//         return s;
//     };
//
//
//     this.fetchMetricInfoById = (node) => {
//         let thisNode = node;
//         let p1 = {metric_id: node.metricId};
//         if (node.metricId in this.cachedNodeInfo) {
//             return $q.resolve(this.cachedNodeInfo[node.metricId]);
//         }
//         return commonService.apiPost('/metrics/metric_info', p1).then((data) => {
//            return data;
//         });
//     };
//
//
//     this.testClick = function () {
//         console.log("testClick");
//         console.log(ctrl.f);
//     };
//
//     this.showInfoClick = (node) => {
//         node.showInfo = !node.showInfo;
//     };
//
//     this.getConsolidatedTrend = (node) => {
//         let numTrendDown = 0;
//
//         if (node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids.forEach((childGuid) => {
//                 let child = this.flatNodes[this.getIndex({guid: childGuid})];
//                 numTrendDown += this.getConsolidatedTrend(child);
//             });
//         } else {
//             if (node.trend === "down") {
//                 numTrendDown += 1;
//             }
//         }
//         return numTrendDown;
//     };
//
//     this.getStatusHtml = (node) => {
//         let s = "";
//         if (node.leaf) {
//             if (node.hasOwnProperty("status")) {
//                 if (node.status !== true) {
//                     s = "Bld: <label class=\"label label-danger\">FAILED</label>";
//                 }
//                 if ((!node.hasOwnProperty("numChildren") && (!node.leaf)) || ((node.numChildren === 0) && !node.leaf)) {
//                     s = "<p style='background-color: white' class=\"\">No Data</p>";
//                 }
//             }
//         } else {
//
//
//
//             //s = "<p><span style='color: green'>&#10003;:</span><b>" + numTrendUp + "</b>" + "&nbsp" ;
//             //s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>";
//             /*if (node.chartName === "BLK_LSV: Latency") {
//                 let u = 0;
//             }*/
//
//             if (node.numChildDegrades) {
//                 s += "<span style='color: red'><i class='fa fa-arrow-down aspect-trend-icon fa-icon-red'>:</i></span>" + node.numChildDegrades + "";
//             }
//             if (node.numChildrenFailed) {
//                 if (node.numChildDegrades) {
//                     s += ",&nbsp";
//                 }
//                 s += "<i class='fa fa-times fa-icon-red'>:</i>" + "<span style='color: black'>" + node.numChildrenFailed + "</span>";
//             }
//         }
//         return s;
//     };
//
//     this.getTrendHtml = (node) => {
//         let s = "";
//         if (node.hasOwnProperty("trend")) {
//             if (node.trend === "up") {
//                 s = "<icon class=\"fa fa-arrow-up aspect-trend-icon fa-icon-green\"></icon>&nbsp";
//             } else if (node.trend === "down") {
//                 s = "<icon class=\"fa fa-arrow-down aspect-trend-icon fa-icon-red\"></icon>&nbsp;";
//             }
//             else if (node.trend === "flat") {
//                 s = "<icon class=\"fa fa-arrow-down aspect-trend-icon\" style=\"visibility: hidden;\"></icon>&nbsp;";
//             }
//         }
//         return s;
//     };
//
//     this.isLeafsParent = (node) => {
//         let isLeafParent = false; // Parent of a leaf
//         if (node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids.forEach((childGuid) => {
//                 let child = this.flatNodes[this.getIndex({guid: childGuid})];
//                 if (child.leaf) {
//                     isLeafParent = true;
//                 }
//             });
//         }
//         return isLeafParent;
//     };
//
//     this.showNonAtomicMetric = (node) => {
//         this.resetGrid();
//         this.mode = "showingNonAtomicMetric";
//         this.currentNode = node;
//         this.currentChartName = node.chartName;
//         this.currentMetricModelName = "MetricContainer";
//         this.expandNode(node).then(() => {
//
//             //this.mode = "showingNonAtomicMetric";
//             this._setupGoodnessTrend(node);
//             this.inner.nonAtomicMetricInfo = node.info;
//             //this.currentNode = null;
//            // this.currentNode = node;
//             // let payload = {
//             //     metric_model_name: "MetricContainer",
//             //     chart_name: node.chartName
//             // };
//             //this.currentChartName = node.chartName;
//             //this.currentMetricModelName = "MetricContainer";
//             console.log("Before getting leaves");
//             if ((node.chartName === "All metrics") || (!this.isLeafsParent(node))) {
//                 return $q.resolve(null);
//             } else {
//                 return $q.resolve(null); // Disable for now
//                 // commonService.apiPost('/metrics/get_leaves', payload, 'test').then((leaves) => {
//                 //
//                 //     let flattenedLeaves = {};
//                 //     this.flattenLeaves("", flattenedLeaves, leaves);
//                 //     $timeout(()=> {
//                 //         this.prepareGridNodes(flattenedLeaves);
//                 //     }, 1000);
//                 //
//                 //     console.log(angular.element($window).width());
//                 //
//                 // });
//
//             }
//
//         });
//
//
//     };
//
//     this.flattenLeaves = function (parentName, flattenedLeaves, node) {
//         let myName = node.name;
//         if (parentName !== "") {
//             myName = parentName + " > " + node.name;
//         }
//         if (!node.leaf) {
//             node.children.forEach((child) => {
//                 this.flattenLeaves(myName, flattenedLeaves, child);
//             });
//         } else {
//             node.lineage = parentName;
//             let newNode = {name: node.name, id: node.id, metricModelName: node.metric_model_name};
//             flattenedLeaves[newNode.id] = newNode;
//         }
//     };
//
//     this.resetGrid = () => {
//         this.grid = [];
//     };
//
//     this.prepareGridNodes = (flattenedNodes) => {
//         let maxRowsInMiniChartGrid = 10;
//         console.log("Prepare Grid nodes");
//         let tempGrid = [];
//         let rowIndex = 0;
//         Object.keys(flattenedNodes).forEach((key) => {
//             if (rowIndex < maxRowsInMiniChartGrid) {
//                 if (tempGrid.length - 1 < rowIndex) {
//                     tempGrid.push([]);
//                 }
//                 tempGrid[rowIndex].push(flattenedNodes[key]);
//                 if (tempGrid[rowIndex].length === this.numGridColumns) {
//                     rowIndex++;
//                 }
//             }
//         });
//         this.grid = tempGrid;
//
//     };
//
//     this._setupGoodnessTrend = (node) => {
//         let values = [{
//                 data: node.goodnessValues
//             }];
//         this.goodnessTrendValues = null;
//         $timeout (() => {
//             this.goodnessTrendValues = values;
//         }, 1);
//
//         this.charting = true;
//
//         this.goodnessTrendChartTitle = node.chartName;
//     };
//
//     this.getChildrenGuids = (node) => {
//         return node.childrenGuids;
//     };
//
//     this.showGoodnessTrend = (node) => {
//         this.mode = "showingGoodnessTrend";
//         this._setupGoodnessTrend(node);
//     };
//
//     this.getIndentHtml = (node) => {
//         let s = "";
//         if (node.hasOwnProperty("indent")) {
//             for(let i = 0; i < node.indent - 1; i++) {
//                 s += "<span style=\"color: white\">&rarr;</span>";
//             }
//             if (node.indent)
//                 s += "<span>&nbsp;&nbsp;</span>";
//         }
//
//         return s;
//     };
//
//     this.editingWeightClick = (info) => {
//         info.editing = true;
//         info.editingWeight = info.weight;
//     };
//
//     this.submitWeightClick = (node, childId, info) => {
//         let payload = {};
//         payload.metric_id = node.metricId;
//         payload.lineage = node.lineage;
//         payload.child_id = childId;
//         payload.weight = info.editingWeight;
//         commonService.apiPost('/metrics/update_child_weight', payload).then((data) => {
//             info.weight = info.editingWeight;
//             this.clearNodeInfoCache();
//             if (node.hasOwnProperty("lineage") && node.lineage.length > 0) {
//                 this.refreshNode(this.getNode(node.lineage[0]));
//             } else {
//                 this.refreshNode(node);
//             }
//         });
//         info.editing = false;
//     };
//
//     this.closeEditingWeightClick = (info) => {
//         info.editing = false;
//     };
//
//
//     this.collapseNode = (node) => {
//         if (node.hasOwnProperty("numChildren")) {
//             this.collapseBranch(node);
//         }
//         node.collapsed = true;
//     };
//
//
//
//     this._insertNewNode = (node, childrenIds, all, alreadyInserted) => {
//         if (childrenIds.length <= 0) {
//             return;
//         }
//         let thisNode = node;
//         let thisAll = all;
//         let childId = childrenIds.pop();
//         let thisChildrenIds = childrenIds;
//         let p1 = {metric_id: childId};
//         if (!node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids = [];
//         }
//
//         return this.fetchMetricInfoById({metricId: childId}).then((data) => {
//             if (!alreadyInserted) {
//                 console.log("!alreadyInserted");
//                 return this.getNodeFromData(data).then((newNode) => {
//                     newNode.guid = this.guid();
//                     thisNode.lineage.forEach((ancestor) => {
//                        newNode.lineage.push(ancestor);
//                     });
//                     newNode.lineage.push(thisNode.guid);
//                     console.log("Added childGuid for node:" + node.chartName);
//                     node.childrenGuids.push(newNode.guid);
//
//                     newNode.indent = thisNode.indent + 1;
//                     let index = this.getIndex(thisNode);
//                     this.flatNodes.splice(index + 1, 0, newNode);
//                     this._insertNewNode(thisNode, thisChildrenIds, thisAll);
//                     newNode.hide = false;
//                     if (thisAll) {
//                         this.expandNode(newNode, thisAll);
//                     }
//                 });
//
//             } else {
//                 console.log("alreadyInserted");
//                 node.childrenGuids.forEach((childGuid) => {
//                    let childNode = this.flatNodes[this.getIndex({guid: childGuid})];
//                    //let childrenIds = JSON.parse(data.children);
//                    childNode.hide = false;
//
//                 });
//
//                 this._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
//             }
//             return $q.resolve(null);
//         });
//
//
//     };
//
//     this.refreshNode = (node) => {
//         let payload = {metric_id: node.metricId};
//         commonService.apiPost('/metrics/metric_info', payload).then((data) => {
//             this.populateNodeInfoCache(data);
//             this.evaluateGoodness(node, data.goodness_values, data.children_goodness_map);
//             this._setupGoodnessTrend(node);
//         });
//         if (node.hasOwnProperty("childrenGuids")) {
//             node.childrenGuids.forEach((childGuid) => {
//                 this.refreshNode(this.getNode(childGuid));
//             });
//         }
//     };
//

//
//     this.collapseBranch = (node, traversedNodes) => {
//         let thisIndex = this.getIndex(node);
//         if (node.hasOwnProperty("numChildren")) {
//             this.hideChildren(node, true);
//             /*
//             for(let i = 1; i <= node.numChildren; i++) {
//                 if (!node.collapsed) {
//                     traversedNodes += this.collapseBranch(this.flatNodes[thisIndex + traversedNodes + 2]);
//                     this.flatNodes[thisIndex + traversedNodes + 1].collapsed = true;
//                     this.flatNodes[thisIndex + traversedNodes + 1].hide = true;
//                 }
//             }*/
//         }
//         return traversedNodes;
//     };
//
//     this.hideChildren = (node, root) => {
//         let totalHides = 0;
//         if (!node) {
//             return 0;
//         }
//         let thisIndex = this.getIndex(node);
//
//
//
//         if (node.hasOwnProperty("numChildren")) {
//             if (!node.childrenFetched) {
//                 return 0;
//             }
//
//             let nextIndex = thisIndex + 1;
//             if ((nextIndex >= this.flatNodes.length) && (!node.collapsed)) {
//                 console.log("Huh!");
//                 return 0;
//             }
//             for(let i = 1; i <= node.numChildren  && (nextIndex < this.flatNodes.length); i++) {
//                 let hides = 0;
//                 if (true) {
//                     hides += this.hideChildren(this.flatNodes[nextIndex], false);
//                 }
//
//                 this.flatNodes[nextIndex].collapsed = true;
//                 this.flatNodes[nextIndex].hide = true;
//                 totalHides += 1 + hides;
//                 nextIndex += hides + 1;
//
//             }
//         }
//         /*
//         if (!root) {
//             this.flatNodes[thisIndex].collapsed = true;
//             this.flatNodes[thisIndex].hide = true;
//             totalHides += 1;
//         }*/
//         return totalHides;
//     };
//
//     isNodeVisible = (node) => {
//         return !node.hide;
//     }
//
// }
//
//
//
//
//
//
