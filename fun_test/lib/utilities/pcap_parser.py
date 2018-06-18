from lib.system.fun_test import *
import pyshark
import os


class PcapParser(object):
    ETHERNET = "ETHERNET"
    IP = "IP"
    PAUSE = "PAUSE"
    PFC = "PFC"
    LAYER_ETH = "layer_eth"
    LAYER_MACC = "layer_macc"

    def __init__(self,
                 filename):
        self.filename = filename
        fun_test.simple_assert(os.path.exists(self.filename), "File %s does not exists locally" % self.filename)

    def __get_captures_from_file(self, display_filter=None):
        return pyshark.FileCapture(self.filename, use_json=True, display_filter=display_filter)

    def _get_key_val(self, key):
        key1 = key.lower().split(' ')
        key1 = '_'.join(key1)
        key1 = key1.replace('.', '_')
        return key1

    def _parse_dict(self, input_dict):
        output_dict = {}
        for key, val in input_dict.iteritems():
            if type(val) is dict:
                output_dict[key] = self._parse_dict(val)
            else:
                key1 = self._get_key_val(key)
                output_dict[key1] = val
        return output_dict

    def parse_jsonlayer(self, layer):
        current_dict = {}
        input_1 = layer._all_fields
        for key, value in input_1.iteritems():
            key1 = self._get_key_val(key)
            if value.__class__.__name__ == "JsonLayer":
                current_dict[key1] = self.parse_jsonlayer(value)
            elif type(value) is dict:
                new_value = self._parse_dict(value)
                current_dict[key1] = new_value
            else:
                current_dict[key1] = value
        return current_dict

    def get_filter_captures(self, display_filter):
        return self.__get_captures_from_file(display_filter)

    def get_first_packet(self, display_filter=None):
        return self.__get_captures_from_file(display_filter)[0]

    def get_last_packet(self, display_filter=None):
        out = self.__get_captures_from_file(display_filter)
        total_packets = len([packet for packet in out])
        return out[total_packets - 1]

    def get_all_packet_fields(self, packet):
        output_dict = {}
        try:
            for layer in packet.layers:
                name = str(layer).split(':')[0]
                layer_name = name.lower().split(' ')
                layer_name = '_'.join(layer_name)
                if layer.__class__.__name__ == "JsonLayer":
                    out = self.parse_jsonlayer(layer)
                output_dict[layer_name] = out
        except Exception as ex:
            fun_test.critical(str(ex))
        return output_dict

    def display_all_packet_fields(self, packet):
        try:
            output_dict = self.get_all_packet_fields(packet)
            for key, val in output_dict.iteritems():
                fun_test.log("output for key %s is %s" % (key, val))
        except Exception as ex:
            fun_test.critical(str(ex))

    def _get_packet_specified(self, first_packet=False, last_packet=False, packet=False):
        output = None
        try:
            fun_test.simple_assert(not (first_packet and last_packet), "Two packets specified, Specify either first"
                                                                       " or last")
            fun_test.simple_assert(not ((first_packet or last_packet) and packet),
                                   message="More than one packet specified to parse. "
                                           "Please select one from first_packet, last_packet, or specify only packet")
            current_packet = packet
            if first_packet:
                current_packet = self.get_first_packet()
            elif last_packet:
                current_packet = self.get_last_packet()

            fun_test.simple_assert(current_packet, "Packet not specified")
            output = current_packet
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def verify_pfc_header_fields(self, first_packet=False, last_packet=False, packet=None, op_code=None, time0=None,
                                 time1=None, time2=None, time3=None, time4=None,
                                 time5=None, time6=None, time7=None):
        cbfc_class_pause_times = 'cbfc_class_pause_times'
        result = False
        try:
            current_packet = self._get_packet_specified(first_packet=first_packet, last_packet=last_packet,
                                                        packet=packet)
            output_dict = self.get_all_packet_fields(current_packet)
            layer = output_dict[self.LAYER_MACC]
            fun_test.simple_assert(layer, "Check %s header fields are present in packet" %
                                   self.PFC)

            if time0 is not None:
                fun_test.test_assert_expected(expected=str(time0),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c0']),
                                              message="Check time0 value in packet")
            if time1 is not None:
                fun_test.test_assert_expected(expected=str(time1),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c1']),
                                              message="Check time1 value in packet")
            if time2 is not None:
                fun_test.test_assert_expected(expected=str(time2),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c2']),
                                              message="Check time2 value in packet")
            if time3 is not None:
                fun_test.test_assert_expected(expected=str(time3),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c3']),
                                              message="Check time3 value in packet")
            if time4 is not None:
                fun_test.test_assert_expected(expected=str(time4),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c4']),
                                              message="Check time4 value in packet")
            if time5 is not None:
                fun_test.test_assert_expected(expected=str(time5),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c5']),
                                              message="Check time5 value in packet")
            if time6 is not None:
                fun_test.test_assert_expected(expected=str(time6),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c6']),
                                              message="Check time6 value in packet")
            if time7 is not None:
                fun_test.test_assert_expected(expected=str(time7),
                                              actual=str(layer[cbfc_class_pause_times]['macc_cbfc_pause_time_c7']),
                                              message="Check time7 value in packet")
            if op_code is not None:
                fun_test.test_assert_expected(expected=str(op_code),
                                              actual=str(layer['macc_opcode']),
                                              message="Check opcode value in packet")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result