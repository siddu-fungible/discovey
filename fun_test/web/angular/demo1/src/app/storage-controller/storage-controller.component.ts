import {Component, Input, OnInit} from '@angular/core';
import {ActionGroup, DpuElement} from "../dpus/dpus.component";
import {FormControl} from "@angular/forms";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {SelectionModel} from "@angular/cdk/collections";
import {MatTableDataSource} from "@angular/material";
import {AddNewVolumeConfigInterface, DataProtectionInterface} from "../workflows/volumes/volumes.component";
import {ApiService} from "../services/api/api.service";
import {CommonService, Controller} from "../services/common/common.service";

export interface ControllerElement {
  id: number;
  health: boolean;
  ip: string;
  port: number;
  active: boolean;
}

export class AddNewControllerConfig {
  id: number = 0;
  ip: string;
  port: number;
}

/*
const ELEMENT_DATA: ControllerElement[] = [
  {id: 0, ip: 'qa-ubuntu-02', port: 50022}
];*/

const ELEMENT_DATA: ControllerElement[] = [];


@Component({
  selector: 'app-storage-controller',
  templateUrl: './storage-controller.component.html',
  styleUrls: ['./storage-controller.component.css'],

  animations: [
    trigger('detailExpand', [
      state('collapsed', style({height: '0px', minHeight: '0', display: 'none'})),
      state('expanded', style({height: '*'})),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
    trigger('enterAnimation', [
      transition(':enter', [
        style({transform: 'translateX(100%)', opacity: 0}),
        animate('500ms')
      ]),
      transition(':leave', [
        style({transform: 'translateX(0)', opacity: 1}),
        animate('500ms')
      ])
    ]),
    trigger('nextStage', [
      state('stage1', style({opacity: 1, 'width': '100%'})),
      state('stage2', style({opacity: 0, 'width': 0, 'visibility': 'hidden', transform: 'translateX(100%)'})),
      transition('stage1 <=> stage2', animate('225ms')),
    ])]
})
export class StorageControllerComponent implements OnInit {
  @Input() action: boolean = true;
  @Input() radioSelection: boolean = true;

  //displayedColumns: string[] = ['select', 'name', 'capacity', 'volumes', 'dpus'];
  displayedColumns: string[] = []; //['name', 'capacity', 'volumes', 'dpus'];

  dataSource = new MatTableDataSource<ControllerElement>(ELEMENT_DATA);
  actionControl = new FormControl();
  actionSelected: string = null;
  selectedRowIndex: number = null;
  selectedElement: string = null;
  selection = new SelectionModel<ControllerElement>(false, []);
  expandedElement: ControllerElement;
  addingNewController: boolean = false;
  newControllerConfig: AddNewControllerConfig = new AddNewControllerConfig();
  healthChecking: boolean = false;
  bgPollCount: number = 0;
  loadOutput: string = null;
  showingApiViewer: boolean = false;

  constructor(private apiService: ApiService, private commonService: CommonService) {
    this.startHealthCheck();
  }


  ngOnInit() {
    if (this.radioSelection) {
      this.displayedColumns = ['active', 'health', 'ip', 'port'];
    } else {
      this.displayedColumns = ['active', 'health', 'name', 'capacity', 'volumes', 'dpus'];
    }
    this.newControllerConfig.ip = "qa-ubuntu-02";
    this.newControllerConfig.port = 50220;
    this.getControllers();
  }

  step = 0;

  setStep(index: number) {
    this.step = index;
  }

  nextStep() {
    this.step++;
  }

  prevStep() {
    this.step--;
  }

  getControllers () {
    this.dataSource.data = [];
    this.apiService.get("/demo/get_controllers").subscribe((response)=> {
      let controllers = response.data;
      controllers.forEach((controller) => {
        const pe: ControllerElement = {id: 0,
          health: false,
          ip: controller.ip,
          port: controller.port,
        active: controller.active};
        this.dataSource.data.push(pe);
        if (pe.active) {
          this.activeControllerSelected(pe, false);
        }
        this.actionSelected = null;
      })

    }, error => {

    });
    /*
    const pe: ControllerElement = {id: 0,
      health: false,
      ip: this.newControllerConfig.ip,
      port: this.newControllerConfig.port};
    this.dataSource.data.push(pe);
    this.dataSource.data = [...this.dataSource.data];
    this.actionSelected = null;
    this.selectedRowIndex = this.dataSource.data.length - 1;
    setTimeout(() => {
      this.selectedRowIndex = null;
    }, 2000);
    this.addingNewController = false;*/


  }

  submit() {
    let payload = {};
    payload["ip"] = this.newControllerConfig.ip;
    payload["port"] = this.newControllerConfig.port;
    this.apiService.post("/demo/add_controller", payload).subscribe((response)=> {
      this.addingNewController = false;
      this.getControllers();

    }, error => {

    });


  }

  /** Whether the number of selected elements matches the total number of rows. */
  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }


  /** Selects all rows if they are not all selected; otherwise clear selection. */
  masterToggle() {
    this.isAllSelected() ?
      this.selection.clear() :
      this.dataSource.data.forEach(row => this.selection.select(row));
  }

  stageAnimationDone($event) {
    if ($event.toState === "stage2") {
    }
    console.log("Animation done");
  }

  public getSelected(): ControllerElement[] {
    return this.selection.selected;
  }

  activeControllerSelected(activeController: ControllerElement, setControllerStatus: boolean = true) {
    let payload = {ip: activeController.ip, port: activeController.port, active: true};
    if (setControllerStatus) {
      this.apiService.post('/demo/set_controller_status', payload).subscribe((response) => {
        this.getControllers();
      }, error => {

      });
    }

    //console.log(this.getSelected());
    //this.getSelected()[0].health = true;
    let c: Controller = new Controller();
    c.id = activeController.id;
    c.health = activeController.health;
    c.ip = activeController.ip;
    c.port = activeController.port;
    this.commonService.setActiveController(c);

  }

  public getActiveController() {
    let result = null;
    let selectedControllers = this.getSelected();
    if (selectedControllers.length > 0) {
      result = selectedControllers[0];
    }
    return result;
  }

  healthCheck() {
     //curl -H "Content-Type: application/json" -X GET http://localhost:50220/api_server/health


    this.dataSource.data.forEach((data) => {
      let url = this.commonService.getBaseUrl() + "/api_server/health";
      this.apiService.get(url).subscribe((response) => {
        console.log(response);
        data.health = response.message === "healthy";
      }, error => {
        data.health = false;
      });
      //console.log(data);

    });

    if (this.healthChecking) {
      setTimeout(() => {
        this.healthCheck();
      }, 5000);
    }
  };


  startHealthCheck() {
    this.healthChecking = true;
    this.healthCheck();
  }

  stopHealthCheck() {
    this.healthChecking = false;
  }

  testBg() {
    let url = "/demo/schedule_fio_job";
    let payload = {};
    this.apiService.post(url, payload).subscribe((response) => {
      let bgExecutionId = response.data;
      let payload = {bg_execution_id: bgExecutionId};
      this.pollStatus(bgExecutionId);
      console.log("BgExecutionID:" + bgExecutionId);
    }, error => {

    });
  }

  pollStatus(executionId) {
    this.bgPollCount++;
    let url = "/demo/bg_job_status";
    let payload = {bg_execution_id: executionId};
    this.apiService.post(url, payload).subscribe((response) => {
      console.log(response.data.status + ":" + response.data.output);
      let executionStatus = response.data.status;
      if (executionStatus !== "PASSED" && executionStatus !== "FAILED") {
        setTimeout(() => {
          this.pollStatus(executionId);
          }, 10000);
      } else {
        this.loadOutput = response.data.output;
      }



    }, error => {

    });


  }


}
