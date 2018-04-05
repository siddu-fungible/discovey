from StcIntPythonPL import *
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.tag_utils as tag_utils
import spirent.methodology.utils.data_model_utils as dm_utils

PKG = "spirent.methodology"


"""
This script finds overlap between two lists of objects and allows you to
change the value of a property of each overlapped object.

Example: In the case of the IPTV multichannel changing methodology,
each iteration, we activate 1 membership per host config. At the end
of each iteration we deactive the memberships we activated.
We do this in a round robin fashion.
This script is used with RunPairScriptCommand, which will get the chained
LeftTagName and RightTagName and put it into the inputjson of this script.
Then we can activate/deactive the IgmpGroupMemberships of each iteration
using this script.
The script finds the IgmpGroupMembership by grabbing the
IgmpGroupMemberships from the left list and right list. Then finding the
overlap between the two.

this json will activate IgmpGroupMemberships given by the tag names
that are chained from MapWhileCommand into RunPairScriptCommand
{
    "scriptFileName": "iptv_set_prop_val.py",
    "methodName": "run",
    "params": {
        "leftRelation": "ParentChild",
        "rightDir": true,
        "rightRelation": "SubscribedGroups",
        "inputValue": "true",
        "property": "Active",
        "objectType": "IgmpGroupMembership"
     }
}
"""


def run(tagname, b, params):
    logger = PLLogger.GetLogger("methodology")
    logger.LogInfo("start creating set property")
    str_err, data = json_utils.load_json(params)
    if str_err != "":
        return str_err

    # make sure we have all params
    str_err = validate_params(data)
    if str_err != "":
        return str_err

    # valid class name
    valid_class, ret_name = dm_utils.validate_classname(data["objectType"])
    if not valid_class:
        return data["objectType"] + " is an invalid class"

    # get left and right list of objects
    left_objects, right_objects, str_err = get_objects(data)
    if str_err != "":
        return str_err

    # get the mid objects using the relation
    left_rel_objs = left_objects[0]. \
        GetObjects(data["objectType"], RelationType(data["leftRelation"],
                                                    data["leftDir"]))
    right_rel_objs = right_objects[0]. \
        GetObjects(data["objectType"], RelationType(data["rightRelation"],
                                                    data["rightDir"]))
    if not left_rel_objs:
        return "No object found from left relation: " + data["leftRelation"]
    if not right_rel_objs:
        return "No object found from right relation: " + data["rightRelation"]

    left_rel_objs = remove_dups(left_rel_objs)
    right_rel_objs = remove_dups(right_rel_objs)

    # get the overlapping mid objects
    hnds, str_err = get_list_overlap(left_rel_objs, right_rel_objs)
    if str_err != "":
        return str_err

    hnd_reg = CHandleRegistry.Instance()
    for hnd in hnds:
        obj = hnd_reg.Find(hnd)
        if obj:
            tag_utils.add_tag_to_object(obj, "iptv_set_prop_val_temp_tag")

    ctor = CScriptableCreator()
    cmd = ctor.CreateCommand(PKG + ".IteratorConfigPropertyValueCommand")
    cmd.Set("CurrVal", data["inputValue"])
    cmd.Set("ClassName", data["objectType"])
    cmd.Set("PropertyName", data["property"])
    cmd.SetCollection("TagList", ["iptv_set_prop_val_temp_tag"])
    cmd.SetCollection("ObjectList", hnds)
    cmd.Execute()
    cmd.MarkDelete()

    tag = tag_utils.get_tag_object("iptv_set_prop_val_temp_tag")
    if tag:
        tag.MarkDelete()

    logger.LogInfo("stop set prop val")
    return ""


def remove_dups(list):
    if not list:
        return None

    map = {}
    for obj in list:
        hnd = obj.GetObjectHandle()
        if hnd not in map:
            map[hnd] = obj
    return map.values()


def validate_params(data):
    # left list
    if "leftTagName" not in data:
        return "Couldn't find leftTagName"
    # right list
    if "rightTagName" not in data:
        return "Couldn't find rightTagName"
    # relation to find mid object of left list
    if "leftRelation" not in data:
        return "Couldn't find leftRelation"
    # relation to find mid object of right list
    if "rightRelation" not in data:
        return "Couldn't find rightRelation"
    # mid object type
    if "objectType" not in data:
        return "Couldn't find objectType"
    # what property we want to modify
    if "property" not in data:
        return "Couldn't find property"
    # what we modify it to
    if "inputValue" not in data:
        return "Couldn't find inputValue"
    # these indicate the direction of the relation
    # it's pushed into RelationType's reverseDir
    if "leftDir" not in data:
        data["leftDir"] = False
    if "rightDir" not in data:
        data["rightDir"] = False
    return ""


def get_objects(data):
    left_objects = tag_utils. \
        get_tagged_objects_from_string_names([data["leftTagName"]])
    right_objects = tag_utils. \
        get_tagged_objects_from_string_names([data["rightTagName"]])
    if not left_objects:
        return None, None, "No left objects found"
    if not right_objects:
        return None, None, "No right objects found"
    if len(left_objects) != 1:
        return None, None, str(len(left_objects)) + \
            " left objects found, but must be exactly 1"
    if len(right_objects) != 1:
        return None, None, str(len(right_objects)) + \
            " right objects found, but must be exactly 1"
    return left_objects, right_objects, ""


# find overlapping objects between two lists
def get_list_overlap(list1, list2):
    all_rel_objs = []
    for obj in list1:
        all_rel_objs.append(obj.GetObjectHandle())
    for obj in list2:
        all_rel_objs.append(obj.GetObjectHandle())
    all_rel_objs.sort()
    hnds = []
    # find objects within both lists
    for i in range(1, len(all_rel_objs)):
        if all_rel_objs[i] == all_rel_objs[i-1]:
            hnds.append(all_rel_objs[i])

    if not hnds:
        return None, "No same objects in both lefts and right's relation objects"
    return hnds, ""
