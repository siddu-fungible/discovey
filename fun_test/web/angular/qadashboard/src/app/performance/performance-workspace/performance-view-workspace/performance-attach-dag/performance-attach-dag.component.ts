import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {Observable} from "rxjs";
import {switchMap} from "rxjs/operators";
import {SelectMode} from "../../../performance.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {LoggerService} from "../../../../services/logger/logger.service";

@Component({
  selector: 'performance-attach-dag',
  templateUrl: './performance-attach-dag.component.html',
  styleUrls: ['./performance-attach-dag.component.css']
})
export class PerformanceAttachDagComponent implements OnInit {
  @Input() flatNode: any = null;
  @Output() closeModal: EventEmitter<boolean> = new EventEmitter();
  selectMode: SelectMode;

  constructor(private modalService: NgbModal, private loggerService: LoggerService) {
  }

  ngOnInit() {
    this.selectMode = SelectMode.ShowAttachDag;
    this.attachDag(document.getElementById('openAttachDag'));
  }

  attachDag(content) {
    new Observable(observer => {
      observer.next(true);
      observer.complete();
      return () => {
      }
    }).pipe(
      switchMap(response => {
        return this.modalService.open(content, {
          ariaLabelledBy: 'modal-attach-dag',
          size: 'lg'
        }).result.then((result) => {
        }, (reason) => {
        });
      })).subscribe(response => {
      console.log("opened attach dag modal");
    }, error => {
      this.loggerService.error("Unable to open edit modal");
    });
  }

  addToDag(): void {
    console.log("added to dag");
  }

  closeAttachModal(): void {
    this.modalService.dismissAll();
    this.closeModal.emit(false);
  }

}
