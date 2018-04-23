from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    GeneratorConfig, StreamBlock


class LoadTccConfiguration(FunTestScript):
    CONFIG_FILE_PATH = fun_test.get_script_parent_directory() + "/spirent_configs/palladium_mac_final.tcc"

    def describe(self):
        self.set_test_details(steps="""
        1. Load "palladium_mac_final.tcc" configuration
        2. Attach ports and apply configuration
        3. Deactivate All Stream Blocks Initially
        """)

    def setup(self):
        global template_obj

        template_obj = SpirentEthernetTrafficTemplate(session_name="Mac Sanity")

        fun_test.test_assert(template_obj, "Initialize Template")

        result = template_obj.setup_existing_tcc_configuration(config_file_path=self.CONFIG_FILE_PATH,
                                                               configure_ports=False)
        fun_test.test_assert(result, "Load Spirent Configuration")

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleanup close session", ignore_on_success=True)


class TestCase(FunTestCase):
    TRAFFIC_DURATION = 30
    MAC_SANITY_STREAM_NAME = "MAC-Sanity-Fixed-Frame"
    FRAME_SIZES = [74, 150, 550, 750, 1500]
    stream_obj = None
    generator_config_obj = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Mac Sanity Mixed Frame Size",
                              steps="""
                              1. Ensure "%s" exists in configuration and activate it
                              2. Create Generator Config and Set duration to %d secs
                              3. Configure Stream Block as follows
                                a. 100 fps
                                b. Include Signature Field
                                c. PRBS fill pattern
                              4. Vary frame size %s bytes
                              5. Validate all sent packets are received on 2nd port
                              6. Ensure NO error stats are going up
                              """ % (self.MAC_SANITY_STREAM_NAME, self.TRAFFIC_DURATION, self.FRAME_SIZES))

    def setup(self):
        self.stream_obj = template_obj.ensure_stream_exists_in_config(stream_block_name=self.MAC_SANITY_STREAM_NAME)
        fun_test.test_assert(self.stream_obj, "%s Stream Found in Config" % self.MAC_SANITY_STREAM_NAME)

        result = template_obj.activate_stream_blocks(stream_block_handles=self.stream_obj.spirent_handle)
        fun_test.test_assert(result, "Activate %s Stream" % self.MAC_SANITY_STREAM_NAME)

        generator_config = {"DurationMode": GeneratorConfig.DURATION_MODE_SECONDS,
                            "Duration": self.TRAFFIC_DURATION,
                            "SchedulingMode": GeneratorConfig.SCHEDULING_MODE_RATE_BASED}

        fun_test.log("Updating Generator Config: %s" % generator_config)

        self.generator_config_obj = GeneratorConfig()
        self.generator_config_obj.update_stream_block_object(**generator_config)

        ports = template_obj.stc_manager.get_port_list()
        fun_test.test_assert(ports, "Get Port List")

        result = template_obj.configure_generator_config(port_handle=ports[0], generator_config_obj=self.generator_config_obj)
        fun_test.test_assert(result, "Generator Configure")

    def run(self):
        stream_config = {"LoadUnit": StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                         "Load": 100,
                         "InsertSig": True,
                         "FillType": StreamBlock.FILL_TYPE_PRBS}

        fun_test.log("Updating Stream Config: %s" % stream_config)
        self.stream_obj.update_stream_block_object(**stream_config)

        ports = template_obj.stc_manager.get_port_list()

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=ports[0],
                                                     update=True)
        fun_test.test_assert(result, "updated Stream Block")

        for frame_size in self.FRAME_SIZES:
            fun_test.add_checkpoint("Test with %d frame size" % frame_size)
            stream_frame = {"FixedFrameLength": frame_size}

            self.stream_obj.update_stream_block_object(**stream_frame)

            result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=ports[0],
                                                         update=True)
            fun_test.test_assert(result, "Update Stream Block Frame Size: %d" % frame_size)

            result = template_obj.enable_generator_configs(generator_configs=[self.generator_config_obj.spirent_handle])
            fun_test.test_assert(result, "Traffic started")

            fun_test.sleep("Waiting for traffic to complete", seconds=40)

            tx_result_handle = template_obj.subscribe_tx_results(parent=template_obj.stc_manager.project_handle)
            fun_test.test_assert(tx_result_handle, "Subscribe Tx Result", ignore_on_success=True)

            rx_result_handle = template_obj.subscribe_rx_results(parent=template_obj.stc_manager.project_handle)
            fun_test.test_assert(rx_result_handle, "Subscribe Rx Result", ignore_on_success=True)

            tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.spirent_handle,
                                                                              subscribe_handle=tx_result_handle)
            fun_test.test_assert(tx_results, "Get Tx Result", ignore_on_success=True)

            rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.spirent_handle,
                                                                              subscribe_handle=rx_result_handle)
            fun_test.test_assert(rx_results, "Get Rx Result", ignore_on_success=True)

            fun_test.test_assert(template_obj.compare_result_attribute(tx_results=tx_results,
                                                                       rx_results=rx_results),
                                 "Validate All sent packets are received. Tx and RX frame count should be same")

            fun_test.test_assert(not template_obj.check_non_zero_error_count(rx_results=rx_results),
                                 "Ensure Error stats are zero")

            fun_test.test_assert(template_obj.clear_subscribed_results(subscribe_handle_list=[tx_result_handle,
                                                                                              rx_result_handle]),
                                 "Clear Subscribe Results", ignore_on_success=True)

    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = LoadTccConfiguration()
    ts.add_test_case(TestCase())
    ts.run()
