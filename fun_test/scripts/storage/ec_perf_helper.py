from lib.system.fun_test import fun_test
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
import re


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    db_log_time = fun_test.shared_variables["db_log_time"]
    num_ssd = fun_test.shared_variables["num_ssd"]
    num_volumes = fun_test.shared_variables["num_volumes"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volumes, fio_job_name=fio_job_name,
                  write_iops=write_iops, read_iops=read_iops, write_throughput=write_bw, read_throughput=read_bw,
                  write_avg_latency=write_latency, read_avg_latency=read_latency, write_90_latency=write_90_latency,
                  write_95_latency=write_95_latency, write_99_latency=write_99_latency,
                  write_99_99_latency=write_99_99_latency, read_90_latency=read_90_latency,
                  read_95_latency=read_95_latency, read_99_latency=read_99_latency,
                  read_99_99_latency=read_99_99_latency, write_iops_unit="ops",
                  read_iops_unit="ops", write_throughput_unit="MBps", read_throughput_unit="MBps",
                  write_avg_latency_unit="usecs", read_avg_latency_unit="usecs", write_90_latency_unit="usecs",
                  write_95_latency_unit="usecs", write_99_latency_unit="usecs", write_99_99_latency_unit="usecs",
                  read_90_latency_unit="usecs", read_95_latency_unit="usecs", read_99_latency_unit="usecs",
                  read_99_99_latency_unit="usecs")

    result = []
    arg_list = post_results.func_code.co_varnames[:12]
    for arg in arg_list:
        result.append(str(eval(arg)))
    result = ",".join(result)
    fun_test.log("Result: {}".format(result))


def configure_ec_volume(storage_controller, ec_info, command_timeout):
    result = True
    if "ndata" not in ec_info or "nparity" not in ec_info or "capacity" not in ec_info:
        result = False
        fun_test.critical("Mandatory attributes needed for the EC volume creation is missing in ec_info dictionary")
        return (result, ec_info)

    if "num_volumes" not in ec_info:
        fun_test.critical("Number of volumes needs to be configured is not provided. So going to configure only one"
                          "EC/LSV volume")
        ec_info["num_volumes"] = 1

    ec_info["uuids"] = {}
    ec_info["volume_capacity"] = {}
    ec_info["attach_uuid"] = {}
    ec_info["attach_size"] = {}

    for num in xrange(ec_info["num_volumes"]):
        ec_info["uuids"][num] = {}
        ec_info["uuids"][num]["blt"] = []
        ec_info["uuids"][num]["ec"] = []
        ec_info["uuids"][num]["jvol"] = []
        ec_info["uuids"][num]["lsv"] = []

        # Calculating the sizes of all the volumes together creates the EC or LSV on top EC volume
        ec_info["volume_capacity"][num] = {}
        ec_info["volume_capacity"][num]["lsv"] = ec_info["capacity"]
        ec_info["volume_capacity"][num]["ndata"] = int(round(float(ec_info["capacity"]) / ec_info["ndata"]))
        ec_info["volume_capacity"][num]["nparity"] = ec_info["volume_capacity"][num]["ndata"]
        # ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8KB value")
            ec_info["volume_capacity"][num]["jvol"] = ec_info["lsv_chunk_size"] * ec_info["volume_block"]["lsv"] * \
                                                      ec_info["jvol_size_multiplier"]

            for vtype in ["ndata", "nparity"]:
                tmp = int(round(ec_info["volume_capacity"][num][vtype] * (1 + ec_info["lsv_pct"])))
                # Aligning the capacity the nearest nKB(volume block size) boundary
                ec_info["volume_capacity"][num][vtype] = ((tmp + (ec_info["volume_block"][vtype] - 1)) /
                                                          ec_info["volume_block"][vtype]) * \
                                                         ec_info["volume_block"][vtype]

        # Setting the EC volume capacity to ndata times of ndata volume capacity
        ec_info["volume_capacity"][num]["ec"] = ec_info["volume_capacity"][num]["ndata"] * ec_info["ndata"]

        # Adding one more block to the plex volume size to add room for super block
        for vtype in ["ndata", "nparity"]:
            ec_info["volume_capacity"][num][vtype] = ec_info["volume_capacity"][num][vtype] + \
                                                     ec_info["volume_block"][vtype]

        # Configuring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            ec_info["uuids"][num][vtype] = []
            for i in range(ec_info[vtype]):
                this_uuid = utils.generate_uuid()
                ec_info["uuids"][num][vtype].append(this_uuid)
                ec_info["uuids"][num]["blt"].append(this_uuid)
                command_result = storage_controller.create_volume(type=ec_info["volume_types"][vtype],
                                                                  capacity=ec_info["volume_capacity"][num][vtype],
                                                                  block_size=ec_info["volume_block"][vtype],
                                                                  name=vtype + "_" + this_uuid[-4:],
                                                                  uuid=this_uuid,
                                                                  command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating {} {} {} {} {} bytes volume on DUT instance".
                                     format(num, i, vtype, ec_info["volume_types"][vtype],
                                            ec_info["volume_capacity"][num][vtype]))

        # Configuring EC volume on top of BLT volumes
        this_uuid = utils.generate_uuid()
        ec_info["uuids"][num]["ec"].append(this_uuid)
        command_result = storage_controller.create_volume(type=ec_info["volume_types"]["ec"],
                                                          capacity=ec_info["volume_capacity"][num]["ec"],
                                                          block_size=ec_info["volume_block"]["ec"],
                                                          name="ec_" + this_uuid[-4:], uuid=this_uuid,
                                                          ndata=ec_info["ndata"],
                                                          nparity=ec_info["nparity"],
                                                          pvol_id=ec_info["uuids"][num]["blt"],
                                                          command_duration=command_timeout)
        fun_test.test_assert(command_result["status"], "Creating {} {}:{} {} bytes EC volume on DUT instance".
                             format(num, ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"][num]["ec"]))
        ec_info["attach_uuid"][num] = this_uuid
        ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["ec"]

        # Configuring LS volume and its associated journal volume based on the script config setting
        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            ec_info["uuids"][num]["jvol"] = utils.generate_uuid()
            command_result = storage_controller.create_volume(type=ec_info["volume_types"]["jvol"],
                                                              capacity=ec_info["volume_capacity"][num]["jvol"],
                                                              block_size=ec_info["volume_block"]["jvol"],
                                                              name="jvol_" + this_uuid[-4:],
                                                              uuid=ec_info["uuids"][num]["jvol"],
                                                              command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} {} bytes Journal volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["jvol"]))

            this_uuid = utils.generate_uuid()
            ec_info["uuids"][num]["lsv"].append(this_uuid)
            command_result = storage_controller.create_volume(type=ec_info["volume_types"]["lsv"],
                                                              capacity=ec_info["volume_capacity"][num]["lsv"],
                                                              block_size=ec_info["volume_block"]["lsv"],
                                                              name="lsv_" + this_uuid[-4:],
                                                              uuid=this_uuid,
                                                              group=ec_info["ndata"],
                                                              jvol_uuid=ec_info["uuids"][num]["jvol"],
                                                              pvol_id=ec_info["uuids"][num]["ec"],
                                                              command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} {} bytes LS volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["lsv"]))
            ec_info["attach_uuid"][num] = this_uuid
            ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["lsv"]
    return (result, ec_info)


def unconfigure_ec_volume(storage_controller, ec_info, command_timeout):
    # Unconfiguring LS volume based on the script config settting
    for num in xrange(ec_info["num_volumes"]):
        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            this_uuid = ec_info["uuids"][num]["lsv"][0]
            command_result = storage_controller.delete_volume(type=ec_info["volume_types"]["lsv"],
                                                              capacity=ec_info["volume_capacity"][num]["lsv"],
                                                              block_size=ec_info["volume_block"]["lsv"],
                                                              name="lsv_" + this_uuid[-4:],
                                                              uuid=this_uuid,
                                                              command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting {} {} bytes LS volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["lsv"]))

            this_uuid = ec_info["uuids"][num]["jvol"]
            command_result = storage_controller.delete_volume(type=ec_info["volume_types"]["jvol"],
                                                              capacity=ec_info["volume_capacity"][num]["jvol"],
                                                              block_size=ec_info["volume_block"]["jvol"],
                                                              name="jvol_" + this_uuid[-4:], uuid=this_uuid,
                                                              command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting {} {} bytes Journal volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["jvol"]))

        # Unconfiguring EC volume configured on top of BLT volumes
        this_uuid = ec_info["uuids"][num]["ec"][0]
        command_result = storage_controller.delete_volume(type=ec_info["volume_types"]["ec"],
                                                          capacity=ec_info["volume_capacity"][num]["ec"],
                                                          block_size=ec_info["volume_block"]["ec"],
                                                          name="ec_" + this_uuid[-4:], uuid=this_uuid,
                                                          command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting {} {}:{} {} bytes EC volume on DUT instance".
                             format(num, ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"][num]["ec"]))

        # Unconfiguring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            for i in range(ec_info[vtype]):
                this_uuid = ec_info["uuids"][num][vtype][i]
                command_result = storage_controller.delete_volume(type=ec_info["volume_types"][vtype],
                                                                  capacity=ec_info["volume_capacity"][num][vtype],
                                                                  block_size=ec_info["volume_block"][vtype],
                                                                  name=vtype + "_" + this_uuid[-4:], uuid=this_uuid,
                                                                  command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting {} {} {} {} {} bytes volume on DUT instance".
                                     format(num, i, vtype, ec_info["volume_types"][vtype],
                                            ec_info["volume_capacity"][num][vtype]))


def compare(actual, expected, threshold, operation):
    if operation == "lesser":
        return actual < (expected * (1 - threshold)) and ((expected - actual) > 2)
    else:
        return actual > (expected * (1 + threshold)) and ((actual - expected) > 2)


def fetch_nvme_device(end_host, nsid):
    lsblk_output = end_host.lsblk("-b")
    fun_test.simple_assert(lsblk_output, "Listing available volumes")
    result = {'status': False}
    for volume_name in lsblk_output:
        match = re.search(r'nvme\dn{}'.format(nsid), volume_name, re.I)
        if match:
            result['volume_name'] = match.group()
            result['nvme_device'] = "/dev/{}".format(result['volume_name'])
            result['status'] = True
    return result
