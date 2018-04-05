from StcIntPythonPL import *
import spirent.methodology.results.drv_utils as drv_utils

PKG = "spirent.methodology"

"""
Save DRV to table
"""


def saveDrvToDb(tagname, b, params):
    drv_list = drv_utils.get_drv(["CustomDrv"])
    if len(drv_list) != 1:
        return ""
    err = drv_utils.save_to_db(drv_list[0], "SUMMARY", "CustomDrvTbl")
    if err:
        print "Error: " + str(err)
    return ""
