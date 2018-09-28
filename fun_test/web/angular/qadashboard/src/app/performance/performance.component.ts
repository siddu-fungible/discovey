import {Component, OnInit} from '@angular/core';
import {ApiService} from "../services/api/api.service";
import {LoggerService} from "../services/logger/logger.service";

@Component({
  selector: 'app-performance',
  templateUrl: './performance.component.html',
  styleUrls: ['./performance.component.css']
})
export class PerformanceComponent implements OnInit {
  numGridColumns: number;
  lastStatusUpdateTime: any;
  mode: string;
  jenkinsJobIdMap: any;
  buildInfo: any;
  flatNodes: any;
  metricMap: any;
  cachedNodeInfo: any;
  goodnessTrendValues: any;
  inner: any;
  currentNodeChildrenGuids: any;
  validDates: any;
  collapsedAll: boolean;
  expandedAll: boolean;


  constructor(private apiService: ApiService, private logger: LoggerService) {
    this.logger.log("Performance component init");
  }

  private componentState: string = "Unknown";
  data: any = [];

  ngOnInit() {
    this.data["rows"] = [['hi', 'hello'], ['how', 'are'], ['you', 'its'], ['been', 'a'], ['long', 'time'], ['also', 'when'], ['where', 'how'], ['are', 'we'], ['meeting', 'if'], ['hey', 'buddy'], ['let', 'go'], ['we', 'will']];
    this.data["headers"] = ['Names', 'Numbers'];
    this.data["all"] = true;

    this.data["totalLength"] = 12;
    this.data["currentPageIndex"] = 1;
    this.data["pageSize"] = 10;


    this.getLastStatusUpdateTime();
    this.numGridColumns = 2;
    if(window.screen.width <= 1441) {
            this.numGridColumns = 2;
    }

    this.mode = null;
    this.fetchJenkinsJobIdMap();

    this.flatNodes = [];
    this.metricMap = {};
    this.cachedNodeInfo = {};

    this.fetchRootMetricInfo("Total", "MetricContainer").then((data) => {
      let metricId = data.metric_id;
      let p1 = {metric_id: metricId};
      this.apiService.post('/metrics/metric_info', p1).subscribe((data) => {
        this.populateNodeInfoCache(data);
        let newNode = this.getNodeFromData(data).then((newNode) => {
          newNode.guid = this.guid();
          newNode.hide = false;
          newNode.indent = 0;
          this.flatNodes.push(newNode);
          // this.expandNode(newNode);
          this.collapsedAll = true;
        });

      },
        error => {
            console.log(error);
            this.componentState = "Error";
          });
      return data;
    });

    this.goodnessTrendValues = null;
    this.inner = {};
    this.inner.nonAtomicMetricInfo = "";
    this.currentNodeChildrenGuids = null;
    this.validDates = null;
  }

  getLastStatusUpdateTime(): void {
        this.apiService.get('/common/time_keeper/' + "last_status_update").subscribe((data) => {
            this.lastStatusUpdateTime = data;
        },
          error => {
            console.log(error);
            this.componentState = "Error";
          });
    }

    fetchJenkinsJobIdMap(): void {
        this.apiService.get('/regression/jenkins_job_id_maps').subscribe((data) => {
            this.jenkinsJobIdMap = data;
            this.apiService.get('/regression/build_to_date_map').subscribe((data) => {
                this.buildInfo = data;
            },
              error => {
            console.log(error);
            this.componentState = "Error";
          });
        },
          error => {
            console.log(error);
            this.componentState = "Error";
          });
    }

    fetchRootMetricInfo(chartName, metricModelName): any {
        let payload = {"metric_model_name": metricModelName, chart_name: chartName};
        return this.apiService.post('/metrics/chart_info', payload).subscribe((data) => {
            return data;
        },
         error => {
        console.log(error);
        this.componentState = "Error";
        });
    }

    populateNodeInfoCache(data): void {
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

    guid(): any {
      function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
          .toString(16)
          .substring(1);
      }
      return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
    }

    expandAllNodes(): void {
        this.flatNodes.forEach((node) => {
            this.expandNode(node, true);
        });
        this.collapsedAll = false;
        this.expandedAll = true;
    }

    collapseAllNodes(): void {
        this.collapseNode(this.flatNodes[0]);
        this.expandedAll = false;
        this.collapsedAll = true;
    };

  expandNode(node, all): any {
        node.collapsed = false;
        if (node.hasOwnProperty("numChildren") && (node.numChildren > 0)) {
            let thisNode = node;
            return this.fetchMetricInfoById(node).then((data) => {
                console.log("Fetching Metrics Info for node:" + node.metricId);
                node.hide = false;
                let childrenIds = JSON.parse(data.children);
                return this._insertNewNode(node, childrenIds, all, node.childrenFetched).then(() => {
                    console.log("Inserted: " + node.chartName);
                    node.childrenFetched = true;
                    return null;
                });

            });
        }
        else {
            return null;
        }
    }

    fetchMetricInfoById(node): any {
        let thisNode = node;
        let p1 = {metric_id: node.metricId};
        if (node.metricId in this.cachedNodeInfo) {
            return this.cachedNodeInfo[node.metricId];
        }
        return this.apiService.post('/metrics/metric_info', p1).subscribe((data) => {
           return data;
        },
          error => {
            console.log(error);
            this.componentState = "Error";
          });
    }

    collapseNode(node): void {
        if (node.hasOwnProperty("numChildren")) {
            // this.collapseBranch(node);
        }
        node.collapsed = true;
    }

    collapseBranch(node, traversedNodes): any {
        let thisIndex = this.getIndex(node);
        if (node.hasOwnProperty("numChildren")) {
            this.hideChildren(node, true);
        }
        return traversedNodes;
    }

    hideChildren(node, root): any {
        let totalHides = 0;
        if (!node) {
            return 0;
        }
        let thisIndex = this.getIndex(node);

        if (node.hasOwnProperty("numChildren")) {
            if (!node.childrenFetched) {
                return 0;
            }

            let nextIndex = thisIndex + 1;
            if ((nextIndex >= this.flatNodes.length) && (!node.collapsed)) {
                console.log("Huh!");
                return 0;
            }
            for(let i = 1; i <= node.numChildren  && (nextIndex < this.flatNodes.length); i++) {
                let hides = 0;
                if (true) {
                    hides += this.hideChildren(this.flatNodes[nextIndex], false);
                }

                this.flatNodes[nextIndex].collapsed = true;
                this.flatNodes[nextIndex].hide = true;
                totalHides += 1 + hides;
                nextIndex += hides + 1;

            }
        }
        return totalHides;
    };

    _insertNewNode(node, childrenIds, all, alreadyInserted): any {
        if (childrenIds.length <= 0) {
            return;
        }
        let thisNode = node;
        let thisAll = all;
        let childId = childrenIds.pop();
        let thisChildrenIds = childrenIds;
        let p1 = {metric_id: childId};
        if (!node.hasOwnProperty("childrenGuids")) {
            node.childrenGuids = [];
        }

        return this.fetchMetricInfoById({metricId: childId}).then((data) => {
            if (!alreadyInserted) {
                console.log("!alreadyInserted");
                return this.getNodeFromData(data).then((newNode) => {
                    newNode.guid = this.guid();
                    thisNode.lineage.forEach((ancestor) => {
                       newNode.lineage.push(ancestor);
                    });
                    newNode.lineage.push(thisNode.guid);
                    console.log("Added childGuid for node:" + node.chartName);
                    node.childrenGuids.push(newNode.guid);

                    newNode.indent = thisNode.indent + 1;
                    let index = this.getIndex(thisNode);
                    this.flatNodes.splice(index + 1, 0, newNode);
                    this._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
                    newNode.hide = false;
                    if (thisAll) {
                        this.expandNode(newNode, thisAll);
                    }
                });

            } else {
                console.log("alreadyInserted");
                node.childrenGuids.forEach((childGuid) => {
                   let childNode = this.flatNodes[this.getIndex({guid: childGuid})];
                   //let childrenIds = JSON.parse(data.children);
                   childNode.hide = false;

                });

                this._insertNewNode(thisNode, thisChildrenIds, thisAll, alreadyInserted);
            }
            return null;
        });
    }

    getIndex(node): any {
        let index = this.flatNodes.map(function(x) {return x.guid;}).indexOf(node.guid);
        return index;
    }

    getNodeFromData(data): any {
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
            numChildrenPassed: data.num_children_passed,
            numChildrenFailed: data.last_num_build_failed,
            lastBuildStatus: data.last_build_status,
            numLeaves: data.num_leaves,
            childrenScoreMap: {},
            status: false,
            numChildren: null

        };
        this.metricMap[newNode.metricId] = {chartName: newNode.chartName};
        if (newNode.info === "") {
            newNode.info = "<p>Please update the description</p>";
        }

        let dateRange = this.getDateRange();
        let fromDate = dateRange[0];
        let toDate = dateRange[1];
        return this.fetchScores(data.metric_id, fromDate.toISOString(), toDate.toISOString()).then((scoreData) => {
            newNode.childrenScoreMap = scoreData["children_score_map"];
            this.evaluateScores(newNode, scoreData["scores"]);
            newNode.childrenWeights.forEach((info, childId) => {
                newNode.children[childId] = {weight: newNode.childrenWeights[childId], editing: false};
            });

            if (newNode.lastBuildStatus === "PASSED") {
                newNode.status = true;
            } else {
                newNode.status = false;
            }

            let newNodeChildrenIds = JSON.parse(data.children);
            if (newNodeChildrenIds.length > 0) {
                newNode.numChildren = newNodeChildrenIds.length;
            }
            return newNode;
        });
    }

    fetchScores(metricId, fromDate, toDate): any {
        let payload = {};
        payload["metric_id"] = metricId;
        payload["date_range"] = [fromDate, toDate];
        return this.apiService.post('/metrics/scores', payload).subscribe((data) => {
            return data;
        },
          error => {
            console.log(error);
            this.componentState = "Error";
          });
    }

    getDateRange(): any {
        let today = new Date();
        console.log(today);
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
    }

    getYesterday(today): any {
        let yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return yesterday;
    }

    getDateBound(dt, lower): any {
        let newDay = new Date(dt);
        if (lower) {
            newDay.setHours(0, 0, 1);
        } else {
            newDay.setHours(23, 59, 59);
        }
        return newDay;
    }

    evaluateScores(node, scores): void {

        let keys = Object.keys(scores);
        let sortedKeys = keys.sort();
        if (node.chartName === "Total") {
            this.validDates = sortedKeys;
        }

        if (Object.keys(scores).length) {
            let mostRecentDateTimestamp = sortedKeys.slice(-1)[0];
            let mostRecentDate = new Date(mostRecentDateTimestamp);
            console.log(mostRecentDate);
            console.log(scores[mostRecentDateTimestamp].score);
        }
        let goodnessValues = [];
        sortedKeys.forEach((key) => {
            goodnessValues.push(scores[key].score);
        });

        node.goodnessValues = goodnessValues;
        try {
                node.goodness = Number(goodnessValues[goodnessValues.length - 1].toFixed(1));
        } catch (e) {

        }

        node.childrenGoodnessMap = {};
        node.trend = "flat";
        if (goodnessValues.length > 1) {
            let penultimateGoodness = Number(goodnessValues[goodnessValues.length - 2].toFixed(1));
            if (penultimateGoodness > node.goodness) {
                node.trend = "down";
            } else if (penultimateGoodness < node.goodness) {
                node.trend = "up";
            }
            if (Number(goodnessValues[goodnessValues.length - 1].toFixed(1)) === 0) {
                node.trend = "down";
            }
        }
        console.log("Node: " + node.chartName + " Goodness: " + node.goodness);
    }

  doSomething1(): void {
    console.log("Doing Something1");
    let payload = {"metric_id": 122, "date_range": ["2018-04-01T07:00:01.000Z", "2018-09-13T06:59:59.765Z"]};
    this.apiService.post('/metrics/scores', payload).subscribe(response => {
        console.log(response.data);
        this.componentState = response.message;
      },
      error => {
        console.log(error);
        this.componentState = "Error";
      });

  }

  getComponentState(): string {
    return this.componentState;
  }
counter(i: number) {
    return new Array(i);
  }


  setValues(pageNumber): void {
    this.data["rows"] = [['hi', 'hello'], ['how', 'are']];
    this.data["headers"] = ['Names', 'Numbers'];
    this.data["all"] = false;
    this.data["totalLength"] = 14;
    this.data["currentPageIndex"] = pageNumber;
    this.data["pageSize"] = this.data["rows"].length;

  }


}
