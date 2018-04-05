from StcIntPythonPL import *

import json
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.data_model_utils as dm_utils


def finalize_ctcc_json(TagName, TaggedObjs, Params):
    '''
    Param ignored
    '''

    # TagName ignored
    # TaggedObjs ignored

    # finalize CTCC
    err, obj_list = dm_utils.get_class_objects(
        [], ["DdosConfigLoop"],
        "spirent.methodology.CreateTemplateConfigCommand", enable_recur_search=False)
    if err != "":
        err = "Failed to get bll object"
        return err

    logger = PLLogger.GetLogger('methodology')
    for obj in obj_list:
        val = obj.Get("InputJson")
        err, j_val = json_utils.load_json(val)
        if err:
            return "Failed to get_json_val_from_string: " + val
        # initialize pdu reference dictionaries
        t_ref = {}
        n_ref = {}
        # step through the CTCC frame config json, always at operationList[0]
        for ctcc_obj in j_val["modifyList"][0]["operationList"][0][
                "pduBuilder"]["pduData"]["pdu_list"]:
            enable_flag = ctcc_obj.get("enable", True)
            pdu = ctcc_obj["pdu"]
            if pdu == "ipv4:IPv4":
                # always grab the IPv4 info, even if the PDU is disabled
                # because this will contain the user configured source/dest IPs
                # ipv4 = ctcc_obj
                t_ref["ipv4"] = ctcc_obj
                n_ref[ctcc_obj["name"]] = ctcc_obj
                continue
            if not enable_flag:
                continue
            # logger.LogError(ctcc_obj["pdu"])
            if pdu == "ethernet:EthernetII":
                t_ref["eth"] = ctcc_obj
            elif pdu == "ipv6:IPv6":
                t_ref["ipv6"] = ctcc_obj
            elif pdu == "udp:Udp":
                t_ref["udp"] = ctcc_obj
            elif pdu == "tcp:Tcp":
                t_ref["tcp"] = ctcc_obj
            elif pdu == "arp:ARP":
                t_ref["arp"] = ctcc_obj
            elif pdu == "icmp:Icmp":
                t_ref["icmp"] = ctcc_obj
            elif pdu == "icmp:IcmpDestUnreach":
                t_ref["icmp_du"] = ctcc_obj
            elif pdu == "icmpv6:NeighborSolicitation":
                t_ref["ndp"] = ctcc_obj
            else:
                logger.LogWarn(pdu + " not handled")
            n_ref[ctcc_obj["name"]] = ctcc_obj
        # perform some copies now, if DST_PROTO and SRC_PROTO
        # if arp and eth:
        if "arp" in t_ref and "eth" in t_ref:
            t_ref["arp"]["property_data"]["senderHwAddr"] = \
                t_ref["eth"]["property_data"]["srcMac"]
            t_ref["arp"]["property_data"]["targetHwAddr"] = \
                t_ref["eth"]["property_data"]["dstMac"]
            # we always have IPv4 so copy that stuff too
            t_ref["arp"]["property_data"]["senderPAddr"] = \
                t_ref["ipv4"]["property_data"]["sourceAddr"]
            t_ref["arp"]["property_data"]["targetPAddr"] = \
                t_ref["ipv4"]["property_data"]["destAddr"]
        if "ndp" in t_ref and "eth" in t_ref:
            t_ref["ndp"]["pdu_data"][0]["pdu_data"][0]["property_data"]["value"] = \
                t_ref["eth"]["property_data"]["srcMac"].replace(':', '')
        if "icmp_du" in t_ref and "eth" in t_ref:
            t_ref["icmp_du"]["pdu_data"][0]["pdu_data"][0]["property_data"]["sourceAddr"] = \
                t_ref["ipv4"]["property_data"]["destAddr"]
            t_ref["icmp_du"]["pdu_data"][0]["pdu_data"][0]["property_data"]["destAddr"] = \
                t_ref["ipv4"]["property_data"]["sourceAddr"]
        for op_obj in j_val["modifyList"][0]["operationList"]:
            addOb = op_obj.get("addObject", False)
            propVal = op_obj.get("propertyValue", False)
            if addOb and addOb["enable"]:
                # always at operationList[2,3,4,5,6,7] so happens after propVal handling (below)
                # provided we're looking at an enabled addObject (modifier)...
                # copy stuff to the Data field for RangeModifiers
                if addOb["className"] == "RangeModifier":
                    # split the ref into the pdu's name and the remainder of the reference string
                    offName, offRef = addOb["propertyValueList"]["OffsetReference"].split(".", 1)
                    targpdu = n_ref.get(offName, False)
                    if targpdu:
                        # check for specific offRefs here (FIXME: can this be made generic?)
                        if offRef == "sourceAddr":
                            addOb["propertyValueList"]["Data"] = \
                                targpdu["property_data"]["sourceAddr"]
                        elif offRef == "ipData.ipHdr.destAddr":
                            addOb["propertyValueList"]["Data"] = \
                                targpdu["pdu_data"][0]["pdu_data"][0]["property_data"]["destAddr"]
                        elif offRef == "ipData.ipHdr.sourceAddr":
                            addOb["propertyValueList"]["Data"] = \
                                targpdu["pdu_data"][0]["pdu_data"][0][
                                    "property_data"]["sourceAddr"]
                        elif offRef == "sourcePort":
                            addOb["propertyValueList"]["Data"] = \
                                targpdu["property_data"]["sourcePort"]
                        elif offRef == "destPort":
                            if targpdu["pdu"] == "tcp:Tcp":
                                addOb["propertyValueList"]["Data"] = \
                                    targpdu["property_data"]["destPort"]
                            else:
                                # udp has a slightly different format
                                addOb["propertyValueList"]["Data"] = \
                                    targpdu["property_data"]["destPort"]["destPort"]
                        else:
                            logger.LogWarn(offName + "." + offRef + ": Data property not set")
                # FIXME: Would be nice to copy _something_ to the Seed field for RandomModifiers
                # elif addOb["className"] == "RandomModifier":
            elif propVal:
                # always at operationList[1] handle attack specific stuff
                pvlName = propVal["propertyValueList"]["name"]
                if pvlName == "LAND" and "tcp" in t_ref:
                    # LAND: source ip & port must be set to dest ip & port
                    t_ref["ipv4"]["property_data"]["sourceAddr"] = \
                        t_ref["ipv4"]["property_data"]["destAddr"]
                    t_ref["tcp"]["property_data"]["sourcePort"] = \
                        t_ref["tcp"]["property_data"]["destPort"]
        # put the InputJson back into the CTCC
        obj.Set("InputJson", json.dumps(j_val))

    return err
