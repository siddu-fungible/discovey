from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.templates.storage.likv_template import LikvTemplate
from lib.host.storage_controller import StorageController

# fun_test.enable_debug()
topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        }

    }
}


class IkvPerformance(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM
                              """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        # topology_obj_helper.save(file_name="/tmp/pickle.pkl")
        # topology = topology_obj_helper.load(file_name="/tmp/pickle.pkl")
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Ensure deploy is successful")

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="LIKV Performance",
                              steps="""
                              1. Create 3 Storage Volumes.
                              2. Perform likv calc vol size.
                              3. Create likv store, open likv store.
                              4. Read performance parameters from json file.
                              5. Generate key value pairs for different size and perform put, get and delete and 
                                 validate retrieved data.""")

    def setup(self):
        pass

    def cleanup(self):
        dut_instance = fun_test.shared_variables["topology"].get_dut_instance(index=0)

        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name="f1.log.txt")
        fun_test.scp(source_ip=dut_instance.host_ip,
                     source_file_path=dut_instance.F1_LOG,
                     source_username=dut_instance.ssh_username,
                     source_password=dut_instance.ssh_password,
                     source_port=dut_instance.ssh_port,
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="F1 Log", filename=artifact_file_name)

    # validate retrieved data

    def ikv_performance(self, size, duration, ikv_obj):
        result = collections.OrderedDict()
        expected_cmd_duration = 2 if size < (16 << 10) else 6
        result['Data Size'] = size
        result["Duration (sec)"] = duration

        # open_ikv = ikv_obj.open()
        # fun_test.test_assert(open_ikv['status'], message="Open likv store with ID: {}".format(ikv_obj.volume_id))
        # fun_test.simple_assert(open_ikv['data']['status'] == 0, message="Open likv response")

        generator = ikv_obj.kv_generator(size=size, max_time=duration / 3)
        key_value_store = [{'key_hex': k, 'value_hex': v} for k, v in generator]

        store_len = len(key_value_store)
        fun_test.test_assert(store_len,
                             message="No of key value pairs generated for size {1}bytes: {0}".format(store_len, size))

        # perform put action on likv store
        put_count = 0
        ikv_obj.storage_controller_obj.verbose = False
        timer = FunTimer(duration)
        while not timer.is_expired() and put_count < store_len:
            put_response = ikv_obj.put(key_hex=key_value_store[put_count]['key_hex'],
                                       value_hex=key_value_store[put_count]['value_hex'],
                                       expected_timeout=expected_cmd_duration)
            if put_response['status']:
                if put_response['data']['status'] == ikv_obj.LIKV_STATUS_SUCCESS:
                    put_count += 1
                else:
                    fun_test.log("Check Put performed for key: {0} value: {1}".format(
                                       key_value_store[put_count]['key_hex'],
                                       key_value_store[put_count]['value_hex']))

        result['Puts/sec'] = "{0:.2f}".format(put_count / float(duration))
        fun_test.test_assert(put_count, message="No of puts performed for size {0}bytes: {1}".format(size, put_count))

        # put remaining key values
        additional_puts = put_count + 250
        ulimit = additional_puts if additional_puts < store_len else store_len
        key_value_store1 = key_value_store[put_count:ulimit]
        key_value_store = key_value_store[:ulimit]
        store_len = len(key_value_store)
        for i in key_value_store1:
            leftover_insert = ikv_obj.put(key_hex=i['key_hex'],
                                          value_hex=i['value_hex'],
                                          expected_timeout=expected_cmd_duration)
            if not leftover_insert['status']:
                key_value_store.remove(i)

        del key_value_store1

        get_count = 0
        timer = FunTimer(duration)
        while not timer.is_expired():
            get_response = ikv_obj.get(key=key_value_store[get_count]['key_hex'])
            if get_response['status']:
                fun_test.test_assert_expected(actual=key_value_store[get_count]['value_hex'],
                                              expected=get_response['data']['value'],
                                              ignore_on_success=True,
                                              message="Compare retrieved data with generated data for shasum: {}".
                                              format(key_value_store[get_count]['key_hex']))
                get_count += 1
            else:
                fun_test.simple_assert(get_response['data']['status'] == ikv_obj.LIKV_STATUS_SUCCESS,
                                       message="Retrieve data using get for key: {}".format(
                                           key_value_store[put_count]['key_hex']))
        result['Gets/sec'] = "{0:.2f}".format(float(get_count) / float(duration))
        fun_test.test_assert(get_count, message="No of gets performed for size {0}bytes:  {1}".format(size, get_count))

        bytes_per_sec = (get_count * size) / duration
        fun_test.test_assert(bytes_per_sec, message="Get performed at rate: {}bytes/sec".format(bytes_per_sec))

        # perform delete
        timer = FunTimer(duration)
        delete_count = 0
        while not timer.is_expired() and (delete_count < store_len):
            delete_response = ikv_obj.delete_value(key=key_value_store[delete_count]['key_hex'])
            if delete_response['status']:
                delete_count += 1

        result['Deletes/sec'] = "{0:.2f}".format(float(delete_count) / float(duration))
        ikv_obj.storage_controller_obj.verbose = True
        ikv_stats = ikv_obj.storage_controller_obj.peek(props_tree="stats/likv")
        fun_test.simple_assert(ikv_stats['status'], message="Peek likv stats")
        ikv_vol_id = str(ikv_obj.volume_id)
        result['tombs'] = ikv_stats['data'][ikv_vol_id]['tombs']
        result['rehash'] = ikv_stats['data'][ikv_vol_id]['rehash']
        result['LIKV used space'] = ikv_stats['data'][ikv_vol_id]['LIKV used space']
        fun_test.sleep(message="volume resizing", seconds=3)
        # close_ikv = ikv_obj.close()
        # fun_test.test_assert(close_ikv['      data']['status'] == 0,
        #                    message="Close likv store with ID: {}".format(ikv_obj.volume_id))
        return result

    def run(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict)
        # topology = topology_obj_helper.load('/tmp/pickle.pkl')
        # set funos topoplogy
        topology = fun_test.shared_variables["topology"]
        dut_instance = topology.get_dut_instance(index=0)
        dut_instance.restart()

        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))
        test_input_dict = utils.parse_file_to_json(benchmark_file)
        volume_info = test_input_dict['likv_volume_info']
        test_params = test_input_dict["test_params"]

        fun_test.test_assert(dut_instance, "Retrieved dut instance")
        storage_controller = StorageController(mode="storage",
                                               target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)

        ikv_obj = LikvTemplate(volume_info=volume_info,
                               storage_controller_obj=storage_controller,
                               likv_volume_id=volume_info["likv_volume_id"])
        # Attach 3 volumes
        fun_test.test_assert(ikv_obj.create_volumes()['status'], message="Attach BLT Volumes")
        # Enable likv
        fun_test.test_assert(ikv_obj.setup_likv_store()['status'], message="Setup IKV store")

        # open ikv store
        open_ikv = ikv_obj.open()
        fun_test.simple_assert(open_ikv['status'], message="execute command to open ikv")
        fun_test.test_assert(open_ikv['data']['status'] == 0, message='Open likv store')

        table_data = []
        table_header = []
        try:
            for data in test_params:
                fun_test.add_checkpoint("Performance sanity for {}bytes".format(data["ip_size"]))
                response = self.ikv_performance(size=data["ip_size"], duration=data["duration"], ikv_obj=ikv_obj)
                fun_test.test_assert(response['Puts/sec'] >= data["min_put_per_sec"],
                                     message="Check Puts performed per second are greater than min rate")
                fun_test.test_assert(response['Gets/sec'] >= data["min_gets_per_sec"],
                                     message="Check Gets performed per second are greater than min rate")
                fun_test.test_assert(response['Deletes/sec'] >= data["min_delete_per_sec"],
                                     message="Check Deletes performed per second are greater than min")
                if test_params.index(data) < 1:
                    table_header = response.keys()
                table_data.append(response.values())
        except Exception as e:
            raise fun_test.critical(e.message)
        finally:
            if table_header:
                fun_test.add_table(panel_header="Likv performance table",
                                   table_name="Performance for Put, Get and Delete calls",
                                   table_data={"headers": table_header, "rows": table_data})


if __name__ == "__main__":
    myscript = IkvPerformance()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
