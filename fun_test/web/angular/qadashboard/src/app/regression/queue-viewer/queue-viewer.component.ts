import { Component, OnInit } from '@angular/core';
import {ApiService} from "../../services/api/api.service";
import {Observable, of, interval, timer} from "rxjs";
import {switchMap, switchMapTo} from "rxjs/operators";
import {LoggerService} from "../../services/logger/logger.service";
import {UserService} from "../../services/user/user.service";

class JobSpec {
  suite_type: string;
  script_path: string;
  suite_path: string;
  email: string;

}


class QueueEntry {
  job_id: number;
  job_spec: JobSpec;
  priority: number;
  test_bed_type: string;
}



@Component({
  selector: 'app-queue-viewer',
  templateUrl: './queue-viewer.component.html',
  styleUrls: ['./queue-viewer.component.css']
})
export class QueueViewerComponent implements OnInit {
  priorityCategories = ["high", "normal", "low"];
  priorityRanges: object = {};
  queueOccupancy = {};
  highPriorityQueueOccupancy: QueueEntry[] = [];
  normalPriorityQueueOccupancy: QueueEntry[] = [];
  lowPriorityQueueOccupancy: QueueEntry[] = [];
  userMap: any = null;
  constructor(private apiService: ApiService, private loggerService: LoggerService, private userService: UserService) { }

  ngOnInit() {
    this.priorityCategories.forEach(category => {
      this.queueOccupancy[category] = [];
    });

    this.getQueueInfo().subscribe(response => {
    });

    this.userService.getUserMap().subscribe(response => {
      this.userMap = response;
    }, error => {
      this.loggerService.error("Unable to fetch user map");
    })

  }

  getQueueInfo(): Observable<boolean> {
    return new Observable(observer => {
      observer.next(true);

      //observer.complete();
      //observer.error("Error");
      return () => {
      };
    }).pipe(switchMap(() => {
      return this.getPriorityRanges();
    }), switchMap(()=> {
      return timer(0, 5000).pipe(switchMap ( () => {
        return this.getCurrentQueueOccupancy();
      }))
    }));
  }


  getPriorityRanges(): Observable<boolean> {
    return this.apiService.get('/regression/scheduler/queue_priorities').pipe(switchMap((response) => {
      let responseData = response.data;
      let ranges = responseData.RANGES;
      for (let key in ranges) {
        let [low, high] = ranges[key];
        this.priorityRanges[key] = {low: low, high: high};
        let i = 0;
      }
      return of(true);
    }));

  }

  getPriorityCategory(priority): string {
    let category: string = null;
    for (let key in this.priorityRanges) {
      if (priority >= this.priorityRanges[key].low && priority <= this.priorityRanges[key].high) {
        category = key;
        break;
      }
    }
    return category;
  }

  getCurrentQueueOccupancy(): Observable<boolean> {

    return this.apiService.get('/regression/scheduler/queue').pipe(switchMap(response => {

      this.priorityCategories.forEach((category) => {
        this.queueOccupancy[category] = [];
      });

      let queueOccupancy = response.data;
      for (let i = 0; i < queueOccupancy.length; i++) {
        let oneQueueEntry = queueOccupancy[i] as QueueEntry;
        const category = this.getPriorityCategory(oneQueueEntry.priority);
        let categoryLower = category.toLowerCase();
        if (categoryLower === 'normal') {
          this.queueOccupancy['normal'].push(oneQueueEntry);
        } else if (categoryLower === 'high') {
          this.queueOccupancy['high'].push(oneQueueEntry);
        } else if (categoryLower === 'low') {
          this.queueOccupancy['low'].push(oneQueueEntry);
        }
      }
      return of(true);
    }))

  }

  toTitleCase(str) {
    return str.replace(
        /\w\S*/g,
        function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
  }

  moveUpDown(jobId, up=true) {
    let payload = {job_id: jobId};
    if (up) {
      payload["operation"] = "move_up";
    } else {
      payload["operation"] = "move_down";
    }
    this.apiService.post('/regression/scheduler/queue', payload).subscribe(response => {
      if (response.data) {
        this.loggerService.success("Priority modification submitted");
      } else {
        this.loggerService.error("Unable to modify priority");
      }

    }, error => {
      this.loggerService.error(`Unable to change the priority of ${jobId}`);
    })
  }

  moveToTop(jobId) {
    let payload = {job_id: jobId, operation: "move_to_top"};
    this.apiService.post('/regression/scheduler/queue', payload).subscribe(response => {
      this.loggerService.success("Priority modification submitted");
    }, error => {
      this.loggerService.error(`Unable to change the priority of ${jobId} to top`);
    })

  }

  moveToNextQueue(jobId) {
    let payload = {job_id: jobId, operation: "move_to_next_queue"};
    this.apiService.post('/regression/scheduler/queue', payload).subscribe(response => {
      this.loggerService.success("Priority modification submitted");
    }, error => {
      this.loggerService.error(`Unable to change the priority of ${jobId} to top`);
    })
  }

  onDelete(queueEntry) {
    let jobId = queueEntry.job_id;
    let url = "/regression/scheduler/queue/" + jobId;
    if (confirm("Are you sure, you want to delete Job-id: " + jobId)) {
      this.apiService.delete(url).subscribe(response => {
        this.loggerService.success("Delete queue entry request submitted");
        this.getCurrentQueueOccupancy().subscribe();
      }, error => {
        this.loggerService.error("Unable to delete queue entry");
      })
    }
  }

  onChangeSuspend(suspend, queueEntry) {
    let url = "/regression/scheduler/queue/" + queueEntry.job_id;
    let payload = {suspend: suspend};
    this.apiService.put(url, payload).subscribe((response) => {

    }, error => {
      this.loggerService.error("Unable to suspend entry")
    })
  }

  onChangePreEmption(preEmptionAllowed, queueEntry) {
    let url = "/regression/scheduler/queue/" + queueEntry.job_id;
    let payload = {pre_emption_allowed: preEmptionAllowed};
    this.apiService.put(url, payload).subscribe((response) => {

    }, error => {
      this.loggerService.error("Unable to change pre-emption")
    })
  }

}
