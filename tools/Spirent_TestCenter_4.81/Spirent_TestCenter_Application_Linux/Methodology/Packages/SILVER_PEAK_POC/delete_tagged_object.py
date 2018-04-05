from StcIntPythonPL import *
import spirent.methodology.utils.tag_utils as tag_utils


def run(tagname, b, params):
    logger = PLLogger.GetLogger('methodology')
    logger.LogInfo("Running delete_tagged_object script with tag name: " + str(tagname))

    obj_list = tag_utils.get_tagged_objects_from_string_names([tagname])
    for obj in obj_list:
        obj.MarkDelete()

    return ""
