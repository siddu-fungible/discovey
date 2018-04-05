from StcIntPythonPL import *
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.tag_utils as tag_utils
import spirent.methodology.utils.data_model_utils as dm_utils
from collections import defaultdict


PKG = "spirent.methodology"

"""
This file contains utility code for convergence methodology tests
"""


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

    if "costIncrement" not in data:
        data["costIncrement"] = 1

    costIncrement = data["costIncrement"]

    # change cost
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        rtrCfg = dev.GetObject("IsisRouterConfig")
        if not rtrCfg:
            continue
        sysId = rtrCfg.Get("SystemId")
        if sysId == 'null':
            ethIf = dm_utils.get_bottom_level_if(dev)
            sysId = ethIf.Get("SourceMac")
        if sysId == 'null':
            return "unable to determine ISIS SystemId"

        lspList = rtrCfg.GetObjects("IsisLspConfig")
        for lsp in lspList:
            lspSysId = lsp.Get("SystemId")
            if lspSysId != 'null' and sysId != lspSysId:
                continue
            nbrList = lsp.GetObjects("IsisLspNeighborConfig")
            for nbr in nbrList:
                metric = nbr.Get("Metric")
                wideMetric = nbr.Get("WideMetric")
                metric += costIncrement
                wideMetric += costIncrement
                nbr.Set("Metric", metric)
                nbr.Set("WideMetric", wideMetric)

    logger.LogInfo("finished changeConvergenceCost")
    return ""


def validate_changeConvergenceCost(data):
    return ""


"""
Change Convergence Route Category For Tagged Objects
{ PrimaryttEmulatedDevice_Route }
Currently supports following protocol: ISIS
"""


def changeConvergenceRouteCategory(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("running changeConvergenceRouteCategory")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # validate parameters
    str_err = validate_changeConvergenceRouteCategory(data)
    if str_err != "":
        return str_err

    if "RouteCategory" not in data:
        data["RouteCategory"] = "Primary"

    RouteCategory = data["RouteCategory"]

    # change route category
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        rtrCtg = dev.GetObject("RouteCategory")
        rtrCtg = RouteCategory
        dev.Set("RouteCategory", rtrCtg)

    logger.LogInfo("finished changeConvergenceRouteCategory")
    return ""


def validate_changeConvergenceRouteCategory(data):
    return ""

"""
Add Convergence Neighbors
{ peerTagName:PrimaryEgress_ttEmulatedDevice }
Currently supports following protocol: ISIS
"""


def addConvergenceNeighbors(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("running addConvergenceNeighbors")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # validate parameters
    str_err = validate_addConvergenceNeighbors(data)
    if str_err != "":
        return str_err

    peerTagName = data["peerTagName"]
    peerDevices = tag_utils.get_tagged_objects_from_string_names(peerTagName)

    # collect a simulated system id map of neigbhors directly connected
    # to the peer device
    isisNbrSysMap = defaultdict(list)
    for dev in peerDevices:
        rtrCfg = dev.GetObject("IsisRouterConfig")
        # for isis routers
        if rtrCfg:
            sysId = rtrCfg.Get("SystemId")
            if sysId == 'null':
                ethIf = dm_utils.get_bottom_level_if(dev)
                sysId = ethIf.Get("SourceMac")
                if sysId == 'null':
                    return "unable to determine ISIS SystemId"
            # in emulated router LSPs get all neighbor systems
            lspList = rtrCfg.GetObjects("IsisLspConfig")
            for lsp in lspList:
                lspSysId = lsp.Get("SystemId")
                if lspSysId != 'null' and sysId != lspSysId:
                    continue
                nbrList = lsp.GetObjects("IsisLspNeighborConfig")
                for nbr in nbrList:
                    nbrSysId = nbr.Get("NeighborSystemId")
                    isisNbrSysMap[nbrSysId].append(sysId)

    ctor = CScriptableCreator()

    # add any emulated systemIds found above to the tagged devices
    devices = tag_utils.get_tagged_objects_from_string_names(tagname)
    for dev in devices:
        rtrCfg = dev.GetObject("IsisRouterConfig")
        # for isis routers
        if rtrCfg:
            sysId = rtrCfg.Get("SystemId")
            if sysId == 'null':
                ethIf = dm_utils.get_bottom_level_if(dev)
                sysId = ethIf.Get("SourceMac")
                if sysId == 'null':
                    return "unable to determine ISIS SystemId"
            lspList = rtrCfg.GetObjects("IsisLspConfig")
            for lsp in lspList:
                lspSysId = lsp.Get("SystemId")
                if lspSysId == 'null' or sysId == lspSysId:
                    continue
                if lspSysId not in isisNbrSysMap:
                    continue
                nbrList = lsp.GetObjects("IsisLspNeighborConfig")
                lspNbrSysList = []
                for nbr in nbrList:
                    nbrSysId = nbr.Get("NeighborSystemId")
                    lspNbrSysList.append(nbrSysId)
                for peerSysId in isisNbrSysMap[lspSysId]:
                    if peerSysId not in lspNbrSysList:
                        nbrTlv = ctor.Create('IsisLspNeighborConfig', lsp)
                        nbrTlv.Set("NeighborSystemId", peerSysId)

    logger.LogInfo("finished addConvergenceNeighbors")
    return ""


def validate_addConvergenceNeighbors(data):
    return ""
