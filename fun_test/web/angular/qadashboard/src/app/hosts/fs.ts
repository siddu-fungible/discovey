import {f1} from "../../../node_modules/@angular/core/src/render3";

export class Vp {
  index: number;
  utilization: { [timestamp: number]: number } = {};

  constructor(index: number) {
    this.index = index;
  }

  addDebugVpUtil(timestamp: number, value: number) {
    this.utilization[timestamp] = value;
  }

}

export class Core {
  index: number;
  vps: Vp [] = [];

  constructor(index: number, clusterIndex: number) {
    this.index = index;
    let maxVp: number = 4;
    if (clusterIndex === 8) {
      maxVp = 2;
    }
    for (let index = 0; index < maxVp; index++) {
      this.addVp(index);
    }
  }

  addVp(index: number) {
    this.vps.push(new Vp(index));
  }

  addDebugVpUtil(vpIndex, timestamp, value) {
    this.vps[vpIndex].addDebugVpUtil(timestamp, value);
  }

}

//6 * 4, 4 * 2
export class Cluster {
  index: number;
  cores: Core [] = [];
  bamUsage: any = {};

  constructor(index: number) {
    this.index = index;
    let maxCores = 6;
    if (index === 8) {
      maxCores = 4;
    }
    for (let index = 0; index < maxCores; index++) {
      this.addCore(index);
    }

  }

  addCore(index) {
    this.cores.push(new Core(index, this.index));
  }

  addDebugVpUtil(coreIndex, vpIndex, timestamp, value) {
    this.cores[coreIndex].addDebugVpUtil(vpIndex, timestamp, value);

  }

  addBamUsage(poolName, poolKey, timestamp, value) {
    if (!this.bamUsage.hasOwnProperty(poolName)) {
      this.bamUsage[poolName] = {};
      this.bamUsage[poolName][poolKey] = {};
      this.bamUsage[poolName][poolKey][timestamp] = value;
    } else {
      if (!this.bamUsage[poolName].hasOwnProperty(poolKey)) {
        this.bamUsage[poolName][poolKey] = {};
        this.bamUsage[poolName][poolKey][timestamp] = value;
      } else {
       this.bamUsage[poolName][poolKey][timestamp] = value;
      }
    }
  }
}

class F1 {
  clusters: Cluster [] = [];


  constructor() {
    for (let index = 0; index < 8; index++) {
      this.clusters.push(new Cluster(index));
    }
  }

  addDebugVpUtil(clusterIndex, coreIndex, vpIndex, timestamp, value) {
    this.clusters[clusterIndex].addDebugVpUtil(coreIndex, vpIndex, timestamp, value);
  }

  addBamUsage(clusterIndex, poolName, poolKey, timestamp, value) {
    this.clusters[clusterIndex].addBamUsage(poolName, poolKey, timestamp, value);
  }
}

export class Fs {
  f1s: F1 [] = [];
  availablePools: any = {};

  constructor() {
    for (let index = 0; index < 2; index++) {
      this.f1s.push(new F1());
    }
  }

  addDebugVpUtil(f1Index, clusterIndex, coreIndex, vpIndex, timestamp, value) {
    this.f1s[f1Index].addDebugVpUtil(clusterIndex, coreIndex, vpIndex, timestamp, value);
  }

  addBamPools(poolName, poolKey) {
    if (this.availablePools.hasOwnProperty(poolName)) {
      if (!this.availablePools[poolName].includes(poolKey)) {
        this.availablePools[poolName].push(poolKey);
      }
    } else {
      this.availablePools[poolName] = [poolKey];
    }
  }

  addBamUsage(f1Index, clusterIndex, poolName, poolKey, timestamp, value) {
    this.addBamPools(poolName, poolKey);
    this.f1s[f1Index].addBamUsage(clusterIndex, poolName, poolKey, timestamp, value);
  }
}
