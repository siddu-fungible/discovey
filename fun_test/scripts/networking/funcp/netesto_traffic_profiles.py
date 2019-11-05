#
#
# total_flows - List of flows in the profile
# total_duration - Total duration of netesto test
# Flow arguments:
# comment - Description of flow
# test - netperf stream type TCP_RR, TCP_STREAM, TCP_MAERTS etc. More than one stream
#        can be specified seperated by commas
# clients - netperf clients mgmt ip
# servers - netperf server mgmt ip
# servers_t - netperf server data ip
# duration - flow duration
# delay - flow start delay ( from start of test)
# instances - number of netperf instances
# rr_size - request reply size
# burst  - netperf traffic burst size
# interval - netperf burst interval
# tos      - netperf tos
# delay_between_instances - start delay between each instance in the particular flow
# repeat_interval - interval after which the same flow is repeated. The same flow will be started
#                   t = delay + repeat_interval
# repeat_max - Number of times the flow has to be repeated


traffic_profile = {}
traffic_profile['multi_f1_profile'] = {
           "total_flows" : "flow1 flow2 flow3 flow4 flow5",
           "total_duration" : "160",
           "netesto_controller" : "mpoc-server01",
           "flow1" : {
               "test" : "TCP_RR",
               "clients" : "mpoc-server30,mpoc-server34",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "30",
               "delay"    : "0",
               "instances" : "1",
               "rr_size"   : "1M,1",
           },
           "flow2" : {
               "test" : "TCP_RR",
               "clients" : "mpoc-server30,mpoc-server34,mpoc-server45,mpoc-server47",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "30",
               "delay"    : "35",
               "instances" : "1",
               "rr_size"   : "1M,1",
           },
           "flow3" : {
               "test" : "TCP_RR",
               "clients" : "mpoc-server45",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "30",
               "delay"    : "65",
               "instances" : "1",
               "rr_size"   : "1M,1",
           },
          "flow4" : {
               "test" : "TCP_RR",
               "clients" : "mpoc-server30,mpoc-server34,mpoc-server45,mpoc-server47,mpoc-server40",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "30",
               "delay"    : "95",
               "instances" : "1",
               "rr_size"   : "1M,1",
           },
           "flow5" : {
               "test" : "TCP_RR",
               "clients" : "mpoc-server45,mpoc-server47",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "30",
               "delay"    : "125",
               "instances" : "1",
               "rr_size"   : "1M,1",
           }

        }
traffic_profile['workload_mix'] = {
           "total_flows" : "flow1 flow2 flow3",
           "total_duration" : "150",
           "netesto_controller" : "mpoc-server01",
           "flow1" : {
               "comment" : "Run 2 instances each stream at 5 Gbps. Total 10 Gbps",
               "test" : "TCP_STREAM",
               "clients" : "mpoc-server30",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "120",
               "delay"    : "0",
               "instances" : "2",
            },
           "flow2" : {
               "comment" : "Run 4 RR instances bursting at line rate for 2 seconds, periodicity 15 sec, inter-stream 1 sec",
               "test" : "TCP_RR",
               "clients" : "mpoc-server30",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "2",
               "delay"    : "5",
               "instances" : "4",
               "rr_size"   : "1M,1",
               "delay_between_instances" : "1",
               "repeat_interval" : "15",
               "repeat_max" : "4",
           },
           "flow3" : {
               "comment" : "Run 2 instances, each bursting at line rate, each running for 1 sec, periodicity 30 sec",
               "test" : "TCP_RR",
               "clients" : "mpoc-server30",
               "servers" : "mpoc-server44",
               "servers_t" : "mpoc-server44t",
               "duration" : "1",
               "delay"    : "45",
               "instances" : "2",
               "rr_size"   : "800B,1",
               "repeat_interval": "30",
               "repeat_max": "2",
           }
        }

traffic_profile['rr_incast'] = {
           "total_flows" : "flow1 flow2",
           "total_duration" : "80",
           "netesto_controller" : "mpoc-server01",
           "flow1" : {
               "comment" : "5 clients to 1 server incast",
               "test" : "TCP_RR",
               "clients" : "mpoc-server44,mpoc-server40,mpoc-server34,mpoc-server45",
               "servers" : "mpoc-server47",
               "servers_t" : "mpoc-server47t",
               "duration" : "60",
               "delay"    : "10",
               "instances" : "1",
               "rr_size"   : "1M,1",
            },
           "flow2" : {
               "comment" : "RR test every 5 seconds",
               "test" : "TCP_RR",
               "clients" : "mpoc-server30",
               "servers" : "mpoc-server47",
               "servers_t" : "mpoc-server47t",
               "duration" : "5",
               "delay"    : "0",
               "instances" : "1",
               "rr_size"   : "1B,4000B",
               "repeat_interval" : "10",
               "repeat_max" : "5",
           },

        }


traffic_profile['incast_basic'] = {
           "total_flows" : "flow1",
           "total_duration" : "60",
           "netesto_controller" : "mpoc-server01",
           "flow1" : {
               "comment" : "5 clients to 1 server incast",
               "test" : "TCP_RR",
               "clients" : "mpoc-server30,mpoc-server44,mpoc-server40,mpoc-server34,mpoc-server45",
               "servers" : "mpoc-server47",
               "servers_t" : "mpoc-server47t",
               "duration" : "60",
               "delay"    : "0",
               "instances" : "1",
               "rr_size"   : "1M,1",
            },


        }