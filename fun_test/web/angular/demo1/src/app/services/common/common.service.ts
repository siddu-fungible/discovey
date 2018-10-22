import { Injectable } from '@angular/core';

export class Controller {
  id: number;
  health: boolean;
  ip: string;
  port: number;
}

export class TopoF1 {
  name: string;
  dataplane_ip: string;
  mgmt_ip: string;
  mgmt_ssh_port: number;
  storage_agent_port: number;

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
      url = "http://" + this.activeController.ip + ":" + this.activeController.port;
    }
    return url;
  }

}
