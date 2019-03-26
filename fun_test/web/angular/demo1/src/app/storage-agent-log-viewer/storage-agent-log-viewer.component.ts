import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {TopoF1} from "../services/common/common.service";
import {ApiService} from "../services/api/api.service";

@Component({
  selector: 'app-storage-agent-log-viewer',
  templateUrl: './storage-agent-log-viewer.component.html',
  styleUrls: ['./storage-agent-log-viewer.component.css']
})
export class StorageAgentLogViewerComponent implements OnInit, OnDestroy {
  @Input() topoF1: TopoF1 = null;
  content: string = "";
  polling: boolean = false;
  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.polling = true;
    this.retrieveLog();
  }

  ngOnDestroy() {
    this.polling = false;
  }


  retrieveLog() {

    if (this.topoF1) {
      let payload = {container_ip: this.topoF1.mgmt_ip,
      container_ssh_port: this.topoF1.mgmt_ssh_port,
      container_ssh_username: "root",
      container_ssh_password: "fun123",
      file_name: "/storage_agent.log"};
      this.apiService.post("/demo/get_container_logs", payload, false).subscribe((response) => {
        this.content = response.data;
      }, error => {

      });

    }

    if (this.polling) {
      setTimeout(()=> {
      this.retrieveLog();
      }, 5000);

    }

  }

}
