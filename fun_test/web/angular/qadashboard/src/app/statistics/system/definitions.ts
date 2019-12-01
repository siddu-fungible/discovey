import {timestamp} from "rxjs/operators";

class Vp {
  index: number;
  utilization: {[timestamp: number]: number};

  constructor(index: number) {
    this.index = index;
  }

}

class Core {
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
}

//6 * 4, 4 * 2
class Cluster {
  index: number;
  cores: Core [] = [];
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

}
