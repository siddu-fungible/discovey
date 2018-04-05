from StcIntPythonPL import *
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.tag_utils as tag_utils
# from collections import defaultdict

# import pydevd; pydevd.settrace()

from StcPython import StcPython
stc = StcPython()

PKG = "spirent.methodology"

"""
Change enableTeparamsSubTlv
Currently supports following protocol: ISIS
"""


def enableTeparamsSubTlv(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("running enableTeparamsSubTlv")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # validate parameters
    str_err = validate_enableTeparamsSubTlv(data)
    if str_err != "":
        return str_err

    # change cost
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        rtr = dev.GetObject("teparams")
        rtr.Set("SubTlv", 'MAX_BW|MAX_RSV_BW|LOCAL_IP|REMOTE_IP')

    logger.LogInfo("finished enableTeparamsSubTlv")
    return ""


def validate_enableTeparamsSubTlv(data):
    return ""


"""
Change enableTeparamsSubTlv
Currently supports following protocol: ISIS
"""


def enableIsisPrefixSidSubTlvFlag(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("running enableIsisPrefixSidSubTlvFlag")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # validate parameters
    str_err = validate_enableIsisPrefixSidSubTlvFlag(data)
    if str_err != "":
        return str_err

    # change enableIsisPrefixSidSubTlvFlag
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        rtr = dev.GetObject("isisprefixsidsubtlv")
        rtr.Set("Flags", 'PBIT|NBIT')

    logger.LogInfo("finished enableTeparamsSubTlv")
    return ""


def validate_enableIsisPrefixSidSubTlvFlag(data):
    return ""


"""
Add IsisLspNeighbor on R6 MergePoint Router for New IsisLsp created using RouteGenerator
Currently supports following protocol: ISIS
"""


def modifyIsisLspNeighbor(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("running modifyIsisLspNeighbor")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # validate parameters
    str_err = validate_modifyIsisLspNeighbor(data)
    if str_err != "":
        return str_err

    # declare variables
    oldIsisLspConfig = []
    newIsisLspConfig = []
    srIsisLspConfig = []
    isisLspConfig = []
    global oldIsisLspConfig
    global newIsisLspConfig
    global srIsisLspConfig
    global systemId

    # change the parent child relation
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        isisRouterConfigList = dev.GetObjects("IsisRouterConfig")
        for isisRouterConfig in isisRouterConfigList:
            isisLspConfigList = isisRouterConfig.GetObjects("IsisLspConfig")
            for isisLspConfig in isisLspConfigList:
                hostName = isisLspConfig.Get("HostName")
                if hostName == "R1":
                    oldIsisLspConfig = isisLspConfig
                elif hostName == "R3":
                    oldIsisLspConfig = isisLspConfig
                elif hostName == "R6":
                    newIsisLspConfig = isisLspConfig
                elif hostName == "SR-11":
                    srIsisLspConfig = isisLspConfig

    isisLspNeighborConfigList = oldIsisLspConfig.GetObjects("isisLspNeighborConfig")
    oldisisLspNeighborConfig_sim_1 = isisLspNeighborConfigList[len(isisLspNeighborConfigList)-2]
    oldisisLspNeighborConfig_sim_2 = isisLspNeighborConfigList[-1]

    newisisLspNeighborConfigList = newIsisLspConfig.GetObjects("isisLspNeighborConfig")
    newisisLspNeighborConfig_sim_1 = \
        newisisLspNeighborConfigList[len(newisisLspNeighborConfigList)-2]
    newisisLspNeighborConfig_sim_2 = newisisLspNeighborConfigList[-1]

    newisisLspNeighborConfig_sim_1.Set("NeighborSystemId",
                                       oldisisLspNeighborConfig_sim_1.Get("NeighborSystemId"))
    old_TeParams = oldisisLspNeighborConfig_sim_1.GetObject("TeParams")
    new_TeParams = newisisLspNeighborConfig_sim_1.GetObject("TeParams")
    new_TeParams.Set("SubTlv", old_TeParams.Get("SubTlv"))
    new_TeParams.Set("BandwidthUnit", old_TeParams.Get("BandwidthUnit"))
    new_TeParams.Set("TeLocalIpv4Addr", old_TeParams.Get("TeLocalIpv4Addr"))
    new_TeParams.Set("TeRemoteIpv4Addr", old_TeParams.Get("TeRemoteIpv4Addr"))
    new_TeParams.Set("TeMaxBandwidth", old_TeParams.Get("TeMaxBandwidth"))
    new_TeParams.Set("TeRsvrBandwidth", old_TeParams.Get("TeRsvrBandwidth"))
    old_isisAdjSidSubTlv = oldisisLspNeighborConfig_sim_1.GetObject("IsisAdjSidSubTlv")
    new_isisAdjSidSubTlv = newisisLspNeighborConfig_sim_1.GetObject("IsisAdjSidSubTlv")
    new_isisAdjSidSubTlv.Set("Weight", old_isisAdjSidSubTlv.Get("Weight"))
    old_isisSidLabelSubTlv = old_isisAdjSidSubTlv.GetObject("IsisSidLabelSubTlv")
    new_isisSidLabelSubTlv = new_isisAdjSidSubTlv.GetObject("IsisSidLabelSubTlv")
    new_isisSidLabelSubTlv.Set("Value", old_isisSidLabelSubTlv.Get("Value"))
    oldisisLspNeighborConfig_sim_1.Set("ACTIVE", 'FALSE')

    newisisLspNeighborConfig_sim_2.Set("NeighborSystemId",
                                       oldisisLspNeighborConfig_sim_2.Get("NeighborSystemId"))
    old_TeParams = oldisisLspNeighborConfig_sim_2.GetObject("TeParams")
    new_TeParams = newisisLspNeighborConfig_sim_2.GetObject("TeParams")
    new_TeParams.Set("SubTlv", old_TeParams.Get("SubTlv"))
    new_TeParams.Set("BandwidthUnit", old_TeParams.Get("BandwidthUnit"))
    new_TeParams.Set("TeLocalIpv4Addr", old_TeParams.Get("TeLocalIpv4Addr"))
    new_TeParams.Set("TeRemoteIpv4Addr", old_TeParams.Get("TeRemoteIpv4Addr"))
    new_TeParams.Set("TeMaxBandwidth", old_TeParams.Get("TeMaxBandwidth"))
    new_TeParams.Set("TeRsvrBandwidth", old_TeParams.Get("TeRsvrBandwidth"))
    old_isisAdjSidSubTlv = oldisisLspNeighborConfig_sim_2.GetObject("IsisAdjSidSubTlv")
    new_isisAdjSidSubTlv = newisisLspNeighborConfig_sim_2.GetObject("IsisAdjSidSubTlv")
    new_isisAdjSidSubTlv.Set("Weight", old_isisAdjSidSubTlv.Get("Weight"))
    old_isisSidLabelSubTlv = old_isisAdjSidSubTlv.GetObject("IsisSidLabelSubTlv")
    new_isisSidLabelSubTlv = new_isisAdjSidSubTlv.GetObject("IsisSidLabelSubTlv")
    new_isisSidLabelSubTlv.Set("Value", old_isisSidLabelSubTlv.Get("Value"))
    oldisisLspNeighborConfig_sim_2.Set("ACTIVE", 'FALSE')

    oldIpv4IsisRoutesConfigList = oldIsisLspConfig.GetObjects("Ipv4IsisRoutesConfig")
    newIpv4IsisRoutesConfigList = newIsisLspConfig.GetObjects("Ipv4IsisRoutesConfig")
    # oldIsisPrefixSidSubTlv_1 = oldIpv4IsisRoutesConfigList[1].GetObject("IsisPrefixSidSubTlv")
    # newIsisPrefixSidSubTlv_1 = newIpv4IsisRoutesConfigList[0].GetObject("IsisPrefixSidSubTlv")
    oldIsisPrefixSidSubTlv_2 = oldIpv4IsisRoutesConfigList[2].GetObject("IsisPrefixSidSubTlv")
    newIsisPrefixSidSubTlv_2 = newIpv4IsisRoutesConfigList[1].GetObject("IsisPrefixSidSubTlv")
    oldIsisPrefixSidSubTlv_3 = oldIpv4IsisRoutesConfigList[3].GetObject("IsisPrefixSidSubTlv")
    newIsisPrefixSidSubTlv_3 = newIpv4IsisRoutesConfigList[2].GetObject("IsisPrefixSidSubTlv")
    # newIsisPrefixSidSubTlv_1.Set("Value", oldIsisPrefixSidSubTlv_1.Get("Value"))
    newIsisPrefixSidSubTlv_2.Set("Value", oldIsisPrefixSidSubTlv_2.Get("Value"))
    newIsisPrefixSidSubTlv_3.Set("Value", oldIsisPrefixSidSubTlv_3.Get("Value"))
    newIpv4IsisRoutesConfigList[1].Set("Metric", oldIpv4IsisRoutesConfigList[2].Get("Metric"))
    newIpv4IsisRoutesConfigList[1].Set("WideMetric",
                                       oldIpv4IsisRoutesConfigList[2].Get("WideMetric"))
    newIpv4IsisRoutesConfigList[2].Set("Metric", oldIpv4IsisRoutesConfigList[3].Get("Metric"))
    newIpv4IsisRoutesConfigList[2].Set("WideMetric",
                                       oldIpv4IsisRoutesConfigList[3].Get("WideMetric"))
    oldIpv4NetworkBlock_1 = oldIpv4IsisRoutesConfigList[2].GetObject("Ipv4NetworkBlock")
    oldIpv4NetworkBlock_2 = oldIpv4IsisRoutesConfigList[3].GetObject("Ipv4NetworkBlock")
    newIpv4NetworkBlock_1 = newIpv4IsisRoutesConfigList[1].GetObject("Ipv4NetworkBlock")
    newIpv4NetworkBlock_2 = newIpv4IsisRoutesConfigList[2].GetObject("Ipv4NetworkBlock")
    newIpv4NetworkBlock_1.SetCollection("StartIpList",
                                        oldIpv4NetworkBlock_1.GetCollection("StartIpList"))
    newIpv4NetworkBlock_2.SetCollection("StartIpList",
                                        oldIpv4NetworkBlock_2.GetCollection("StartIpList"))
    newIpv4NetworkBlock_1.Set("PrefixLength", oldIpv4NetworkBlock_1.Get("PrefixLength"))
    newIpv4NetworkBlock_2.Set("PrefixLength", oldIpv4NetworkBlock_2.Get("PrefixLength"))
    oldIpv4IsisRoutesConfigList[1].Set("ACTIVE", 'FALSE')
    oldIpv4IsisRoutesConfigList[2].Set("ACTIVE", 'FALSE')
    oldIpv4IsisRoutesConfigList[3].Set("ACTIVE", 'FALSE')

    oldIsisCapabilityTlvList = oldIsisLspConfig.GetObjects("IsisCapabilityTlv")
    newIsisCapabilityTlvList = newIsisLspConfig.GetObjects("IsisCapabilityTlv")
    oldIsissrCapabilitysubTlv = oldIsisCapabilityTlvList[-1].GetObject("IsissrCapabilitysubTlv")
    newIsissrCapabilitysubTlv = newIsisCapabilityTlvList[-1].GetObject("IsissrCapabilitysubTlv")
    newIsissrCapabilitysubTlv.Set("Range", newIsissrCapabilitysubTlv.Get("Range"))
    oldIsisSidLabelSubTlv = oldIsissrCapabilitysubTlv.GetObject("IsisSidLabelSubTlv")
    newIsisSidLabelSubTlv = newIsissrCapabilitysubTlv.GetObject("IsisSidLabelSubTlv")
    newIsisSidLabelSubTlv.Set("Value", oldIsisSidLabelSubTlv.Get("Value"))
    oldIsisSrAlgorithmSubTlv = oldIsisCapabilityTlvList[-1].GetObject("IsisSrAlgorithmSubTlv")
    newIsisSrAlgorithmSubTlv = newIsisCapabilityTlvList[-1].GetObject("IsisSrAlgorithmSubTlv")
    newIsisSrAlgorithmSubTlv.SetCollection("Algorithms",
                                           oldIsisSrAlgorithmSubTlv.GetCollection("Algorithms"))
    oldIsisCapabilityTlvList[1].Set("ACTIVE", 'FALSE')
    oldIsisCapabilityTlvList[-1].Set("ACTIVE", 'FALSE')

    systemId = newIsisLspConfig.Get("SystemId")
    isisLspNeighborConfigList = srIsisLspConfig.GetObjects("isisLspNeighborConfig")
    isisLspNeighborConfigList[0].Set("NeighborSystemId", systemId)
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        isisRouterConfigList = dev.GetObjects("IsisRouterConfig")
        for isisRouterConfig in isisRouterConfigList:
            isisLspConfigList = isisRouterConfig.GetObjects("IsisLspConfig")
            isisLspNeighborConfigList = isisLspConfigList[-1].GetObjects("IsisLspNeighborConfig")
            isisLspNeighborConfigList[-1].Set("NeighborSystemId", systemId)

    logger.LogInfo("finished modifyIsisLspNeighbor")
    return ""


def validate_modifyIsisLspNeighbor(data):
    return ""


def modifyIgpIsisLspNeighbor(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("running modifyIgpIsisLspNeighbor")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # validate parameters
    str_err = validate_modifyIgpIsisLspNeighbor(data)
    if str_err != "":
        return str_err

    # declare variables
    oldIsisLspConfig = []
    newIsisLspConfig = []
    global oldIsisLspConfig
    global newIsisLspConfig
    global srIsisLspConfig
    global systemId

    # change the parent child relation
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        isisRouterConfigList = dev.GetObjects("IsisRouterConfig")
        for isisRouterConfig in isisRouterConfigList:
            isisLspConfigList = isisRouterConfig.GetObjects("IsisLspConfig")
            for isisLspConfig in isisLspConfigList:
                hostName = isisLspConfig.Get("HostName")
                if hostName == "R2":
                    oldIsisLspConfig = isisLspConfig
                elif hostName == "R6":
                    newIsisLspConfig = isisLspConfig
                elif hostName == "SR-11":
                    srIsisLspConfig = isisLspConfig

    isisLspNeighborConfigList = oldIsisLspConfig.GetObjects("isisLspNeighborConfig")
    oldisisLspNeighborConfig_sim_1 = isisLspNeighborConfigList[len(isisLspNeighborConfigList)-2]
    oldisisLspNeighborConfig_sim_2 = isisLspNeighborConfigList[-1]

    newisisLspNeighborConfigList = newIsisLspConfig.GetObjects("isisLspNeighborConfig")
    newisisLspNeighborConfig_sim_1 = \
        newisisLspNeighborConfigList[len(newisisLspNeighborConfigList)-2]
    newisisLspNeighborConfig_sim_2 = newisisLspNeighborConfigList[-1]

    newisisLspNeighborConfig_sim_1.Set("NeighborSystemId",
                                       oldisisLspNeighborConfig_sim_1.Get("NeighborSystemId"))
    old_TeParams = oldisisLspNeighborConfig_sim_1.GetObject("TeParams")
    new_TeParams = newisisLspNeighborConfig_sim_1.GetObject("TeParams")
    new_TeParams.Set("SubTlv", old_TeParams.Get("SubTlv"))
    new_TeParams.Set("BandwidthUnit", old_TeParams.Get("BandwidthUnit"))
    new_TeParams.Set("TeLocalIpv4Addr", old_TeParams.Get("TeLocalIpv4Addr"))
    new_TeParams.Set("TeRemoteIpv4Addr", old_TeParams.Get("TeRemoteIpv4Addr"))
    new_TeParams.Set("TeMaxBandwidth", old_TeParams.Get("TeMaxBandwidth"))
    new_TeParams.Set("TeRsvrBandwidth", old_TeParams.Get("TeRsvrBandwidth"))
    oldisisLspNeighborConfig_sim_1.Set("ACTIVE", 'FALSE')

    newisisLspNeighborConfig_sim_2.Set("NeighborSystemId",
                                       oldisisLspNeighborConfig_sim_2.Get("NeighborSystemId"))
    old_TeParams = oldisisLspNeighborConfig_sim_2.GetObject("TeParams")
    new_TeParams = newisisLspNeighborConfig_sim_2.GetObject("TeParams")
    new_TeParams.Set("SubTlv", old_TeParams.Get("SubTlv"))
    new_TeParams.Set("BandwidthUnit", old_TeParams.Get("BandwidthUnit"))
    new_TeParams.Set("TeLocalIpv4Addr", old_TeParams.Get("TeLocalIpv4Addr"))
    new_TeParams.Set("TeRemoteIpv4Addr", old_TeParams.Get("TeRemoteIpv4Addr"))
    new_TeParams.Set("TeMaxBandwidth", old_TeParams.Get("TeMaxBandwidth"))
    new_TeParams.Set("TeRsvrBandwidth", old_TeParams.Get("TeRsvrBandwidth"))
    oldisisLspNeighborConfig_sim_2.Set("ACTIVE", 'FALSE')

    oldIpv4IsisRoutesConfigList = oldIsisLspConfig.GetObjects("Ipv4IsisRoutesConfig")
    newIpv4IsisRoutesConfigList = newIsisLspConfig.GetObjects("Ipv4IsisRoutesConfig")
    newIpv4IsisRoutesConfigList[1].Set("Metric", oldIpv4IsisRoutesConfigList[1].Get("Metric"))
    newIpv4IsisRoutesConfigList[1].Set("WideMetric",
                                       oldIpv4IsisRoutesConfigList[1].Get("WideMetric"))
    newIpv4IsisRoutesConfigList[2].Set("Metric", oldIpv4IsisRoutesConfigList[2].Get("Metric"))
    newIpv4IsisRoutesConfigList[2].Set("WideMetric",
                                       oldIpv4IsisRoutesConfigList[2].Get("WideMetric"))
    oldIpv4NetworkBlock_1 = oldIpv4IsisRoutesConfigList[1].GetObject("Ipv4NetworkBlock")
    oldIpv4NetworkBlock_2 = oldIpv4IsisRoutesConfigList[2].GetObject("Ipv4NetworkBlock")
    newIpv4NetworkBlock_1 = newIpv4IsisRoutesConfigList[1].GetObject("Ipv4NetworkBlock")
    newIpv4NetworkBlock_2 = newIpv4IsisRoutesConfigList[2].GetObject("Ipv4NetworkBlock")
    newIpv4NetworkBlock_1.SetCollection("StartIpList",
                                        oldIpv4NetworkBlock_1.GetCollection("StartIpList"))
    newIpv4NetworkBlock_2.SetCollection("StartIpList",
                                        oldIpv4NetworkBlock_2.GetCollection("StartIpList"))
    newIpv4NetworkBlock_1.Set("PrefixLength", oldIpv4NetworkBlock_1.Get("PrefixLength"))
    newIpv4NetworkBlock_2.Set("PrefixLength", oldIpv4NetworkBlock_2.Get("PrefixLength"))
    oldIpv4IsisRoutesConfigList[1].Set("ACTIVE", 'FALSE')
    oldIpv4IsisRoutesConfigList[2].Set("ACTIVE", 'FALSE')

    systemId = newIsisLspConfig.Get("SystemId")
    isisLspNeighborConfigList = srIsisLspConfig.GetObjects("isisLspNeighborConfig")
    isisLspNeighborConfigList[0].Set("NeighborSystemId", systemId)
    for dev in devices:
        isisRouterConfigList = dev.GetObjects("IsisRouterConfig")
        for isisRouterConfig in isisRouterConfigList:
            isisLspConfigList = isisRouterConfig.GetObjects("IsisLspConfig")
            isisLspNeighborConfigList = isisLspConfigList[-1].GetObjects("IsisLspNeighborConfig")
            isisLspNeighborConfigList[-1].Set("NeighborSystemId", systemId)

    logger.LogInfo("finished modifyIgpIsisLspNeighbor")
    return ""


def validate_modifyIgpIsisLspNeighbor(data):
    return ""

"""
Change Convergence Route Cost For Tagged Objects
{ costIncrement:1 }
Currently supports following protocol: ISIS
"""


def changeConvergenceCost(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("running changeConvergenceCost")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # validate parameters
    str_err = validate_changeConvergenceCost(data)
    if str_err != "":
        return str_err

    # change cost
    device = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in device:
        isisRouterConfigList = dev.GetObjects("IsisRouterConfig")

    for isisRouterConfig in isisRouterConfigList:
        isisLspConfigList = isisRouterConfig.GetObjects("IsisLspConfig")

    for isisLspConfig in isisLspConfigList:
        isisLspNeighborList = isisLspConfig.GetObjects("IsisLspNeighborConfig")

    for isisLspNeighbor in isisLspNeighborList:
        metric = isisLspNeighbor.Get("Metric")
        wideMetric = isisLspNeighbor.Get("WideMetric")
        metric += 1
        wideMetric += 1
        isisLspNeighbor.Set("Metric", metric)
        isisLspNeighbor.Set("WideMetric", wideMetric)

    logger.LogInfo("finished changeConvergenceCost")
    return ""


def validate_changeConvergenceCost(data):
    return ""
