from StcIntPythonPL import *
import json
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.tag_utils as tag_utils


PKG = "spirent.methodology"
PKG_TRF = PKG + ".traffic"


# JSON input is a dictionary containing the frame_size_list:
# {
#   "enable": true,
#   "frame_size_list": ["128", "256", "512"],
#   "imix_tag_name": "west_imix"
# }
def config_imix_cmd_input(tag_name, b, params):
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("Running config_imix_input")

    target_cmd_class = PKG_TRF + ".createimixdistributioncommand"
    cmd_list = tag_utils.get_tagged_objects_from_string_names(
        tag_name, class_name=target_cmd_class)
    if len(cmd_list) < 1:
        return "No tagged " + target_cmd_class + " commands " + \
            "to configure input for."

    err_str, j_dict = json_utils.load_json(params)
    if err_str != "":
        return "Failed to parse JSON: " + err_str
    if not j_dict.get("enable", False):
        return ""
    imix_tag_name = j_dict.get("imix_tag_name", "")
    if imix_tag_name == "":
        return "imix_tag_name is required."

    frame_size_list = j_dict.get("frame_size_list", [])
    if len(frame_size_list) < 1:
        return "No frame sizes to create imix distributions with."
    plLogger.LogDebug("frame_size_list: " + str(frame_size_list))

    # Build the input
    table = []
    for frame_size in frame_size_list:
        try:
            frame_size = int(frame_size)
        except:
            return "Failed to cast " + str(frame_size) + " as an int."
        table.append({
            "fixedFrameLength": frame_size,
            "weight": 1,
            "frameLengthMode": "FIXED"
        })
    i_list = [{"table": table,
               "tag": imix_tag_name,
               "name": imix_tag_name}]
    i_dict = {
        "imixes": i_list
    }
    plLogger.LogDebug("target cmd input: " + json.dumps(i_dict))
    for cmd in cmd_list:
        cmd.Set("ImixInfo", json.dumps(i_dict))
    return ""
