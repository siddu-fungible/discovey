import {Api} from "../lib/api";

export class Daemon extends Api {
  classType = Daemon;
  url = "/api/v1/daemons";
  name: string;
  daemon_id: number;
  id: number;
  heart_beat_time: string;
  heart_beat_time_timestamp: number;

  serialize(): any {

  }

  deSerialize(data: any): any {
    if (data.hasOwnProperty("name")) {
      this.name = data.name;
    }

    if (data.hasOwnProperty('daemon_id')) {
      this.daemon_id = data.daemon_id;
    }

    if (data.hasOwnProperty('heart_beat_time')) {
      this.heart_beat_time = data.heart_beat_time;
    }

    if (data.hasOwnProperty('heart_beat_time_timestamp')) {
      this.heart_beat_time_timestamp = data.heart_beat_time_timestamp;
    }
  }
}
