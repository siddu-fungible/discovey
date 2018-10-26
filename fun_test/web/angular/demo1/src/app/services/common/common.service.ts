import { Injectable } from '@angular/core';

export class Controller {
  id: number;
  health: boolean;
  ip: string;
  port: number;
}

export class TopoTg {
  name: string;
  mgmt_ip: string;
  dataplane_ip: string;
  mgmt_ssh_port: number;
}

export class TopoF1 {
  name: string;
  dataplane_ip: string;
  mgmt_ip: string;
  mgmt_ssh_port: number;
  storage_agent_port: number;
  tgs: {
    [name: string]: TopoTg;
  }

}



@Injectable({
  providedIn: 'root'
})
export class CommonService {
  activeController: Controller = null;
  constructor() { }

  setActiveController(controller: Controller) {
    this.activeController = controller;
  }

  getActiveController(): Controller {
    return this.activeController;
  }

  getBaseUrl(): string {
    let url = null;
    if (this.activeController) {
      url = "http://" + this.activeController.ip + ":" + this.activeController.port + "/FunCC/v1";
    }
    return url;
  }




}
