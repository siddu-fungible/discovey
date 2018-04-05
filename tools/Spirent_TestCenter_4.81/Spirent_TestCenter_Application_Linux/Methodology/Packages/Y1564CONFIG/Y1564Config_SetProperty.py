from StcIntPythonPL import *
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.tag_utils as tag_utils


PKG = "spirent.methodology"


def enable_streamblocks(tagname, b, params):
    plLogger = PLLogger.GetLogger('methodology')
    plLogger.LogDebug('begin enable_streamblocks custom script')

    input_dict = json_utils.load_json(params)[1]

    if "iteratorTagName" in input_dict:
        iterator_tagname = input_dict["iteratorTagName"]

    iteratorCmd = tag_utils.get_tagged_objects_from_string_names([iterator_tagname], True, True)

    if "setPropTagName" in input_dict:
        setProp_tagname = input_dict["setPropTagName"]

    setPropCmd = tag_utils.get_tagged_objects_from_string_names([setProp_tagname], True, True)

    iteration_num = int(iteratorCmd[0].Get("CurrVal")) - int(iteratorCmd[0].Get("MinVal"))
    key = "table[" + str(iteration_num) + "].enable"
    setPropCmd[0].Set("JsonKey", key)

    plLogger.LogDebug('end enable_streamblocks custom script')
    return ""
