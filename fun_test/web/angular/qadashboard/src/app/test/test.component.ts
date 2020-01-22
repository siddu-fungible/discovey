import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {RegressionService} from "../regression/regression.service";
import {Observable, of, forkJoin} from "rxjs";
import {switchMap} from "rxjs/operators";
import {ApiResponse, ApiService} from "../services/api/api.service";
import {CommonService} from "../services/common/common.service";
import {TestBedService} from "../regression/test-bed/test-bed.service";
import {UserService} from "../services/user/user.service";
import {LoggerService} from "../services/logger/logger.service";

class TreeNode {
  id: number;
  name: string;
  leaf: boolean;
  meta_data: any = {"checked": false};
  children: TreeNode [] = null;

  constructor(props) {
    this.name = props.name;
    this.leaf = props.leaf;
    this.id = props.id;
  }

  addChild(node: TreeNode) {
    if (!this.children) {
      this.children = [];
    }
    this.children.push(node);
    return node;
  }
}

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css'],
})

export class TestComponent implements OnInit {
  tree: TreeNode = null;
  selectedStats: any[] = [];
  selectedStatsSet: any = new Set();

  constructor(private regressionService: RegressionService,
              private apiService: ApiService,
              private loggerService: LoggerService,
              private commonService: CommonService,
              private service: TestBedService,
              private userService: UserService
  ) {
    this.tree = new TreeNode({name: "Stats", leaf: false, id: 0});
    let systemNode = this.tree.addChild(new TreeNode({name: "system", leaf: false, id: 0}));
    let storageNode = this.tree.addChild(new TreeNode({name: "storage", leaf: false, id: 1}));
    let bamNode = systemNode.addChild(new TreeNode({name: "BAM", leaf: false, id: 0}));
    let vpNode = systemNode.addChild(new TreeNode({name: "VP utilization", leaf: false, id: 1}));
    let defaultPool = bamNode.addChild(new TreeNode({name: "default_alloc_pool", leaf: false, id: 0}));
    defaultPool.addChild(new TreeNode({name: "usage_percent", leaf: true, id: 0}));
    vpNode.addChild(new TreeNode({name: "utilization_distribution", leaf: true, id: 0}));
    vpNode.addChild(new TreeNode({name: "utilization_by_cluster", leaf: true, id: 1}));
    storageNode.addChild(new TreeNode({name: "SSD", leaf: true, id: 0}));

  }

  ngOnInit() {
  }

  clicked(flatNode): void {
    console.log(flatNode.lineage);
    console.log(flatNode.treeNode.meta_data.checked);
    if (flatNode.treeNode.meta_data.checked) {
      this.selectedStatsSet.add(flatNode.name);
    } else {
      this.selectedStatsSet.delete(flatNode.name);
    }

    // this.selectedStats = Array.from(this.selectedStatsSet);
  }

  deleteStats(stat): void {
    this.selectedStatsSet.delete(stat);

  }

}
