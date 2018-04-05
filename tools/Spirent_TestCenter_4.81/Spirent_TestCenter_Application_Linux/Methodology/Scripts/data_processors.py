from StcIntPythonPL import *

import spirent.methodology.utils.json_utils as json_utils


def set_processed_prefix_length_dist_list(TagName, TaggedObjs, Params):
    '''
    Param = {
                "table": [[ ], [ ], ... [ ]],
                "is_ipv4": true,
                "class": "spirent.methodology.routing.CreateRouteMixCommand",
                "property": "InputJson",
                "key": "Sequencer.CommandList[2].Children[0].Properties[1].
                            value.table[0].modifyList[0].operationList[1].
                            propertyValue.propertyValueList.PrefixLengthDist"
            }
    '''
    err, d = json_utils.load_json(Params)
    if err != '':
        return err
    s, err = process_prefix_length_dist_input(d['table'], d['is_ipv4'])
    if err is None:
        ctor = CScriptableCreator()
        set_cmd = ctor.CreateCommand('spirent.methodology.SetPropertyCommand')
        set_cmd.SetCollection("TagList", [TagName])
        set_cmd.Set("ClassName", d['class'])
        set_cmd.Set("PropertyName", d['property'])
        set_cmd.Set("JsonKey", d['key'])
        set_cmd.Set("Value", s)
        set_cmd.Execute()
        if set_cmd.Get("PassFailState") != "PASSED":
            err = "Failed to set prefix length distribution property: " + set_cmd.Get("Status")
        set_cmd.MarkDelete()
    return err


def process_prefix_length_dist_input(dist_list, is_ipv4):
    '''
    This data process will convert a python list of tuples (dist_list), where
    each tuple is in the form [prefix_length, percent] into a native BLL property
    form for prefix length distribution lists. A tuple with 0 percent
    value is not required (for an optimized list).  The prefix lengths
    begin at 1 and end at either 32 or 128. For example:

            [["25", "35"], ["28", "25"], ["31", "20"], ["32", "20"]]

    The result is a single string containing all the distribution
    values (percentages) in order of their prefix length. Where no
    prefix length is provided, a 0 is used. For example, the following
    string is the transformation of the list above, and contains a total
    of 32 numbers (assumes is_ipv4 is true):

    "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 35 0 0 25 0 0 20 20"

    is_ipv4 is true if the string should have 32 values, or false if
    it should have 128 values.

    If any prefix length is invalid, a message will be returned indicating
    which prefix lengths are invalid for the IP version chosen.

    If the values do not total exactly 100 (for 100%), then a message will
    be returned indicating the total is not valid.
    '''

    # Note any prefix lengths that are invalid...
    invalid_prefix_lengths = []
    # Convert the list of tuples into a dictionary...
    d = {}
    for (prefix, length) in [(int(p), int(l)) for (p, l) in dist_list]:
        if prefix in d:
            return '', 'Duplicate prefix length of ' + str(prefix) + ' found'
        if prefix < 1 or prefix > (32 if is_ipv4 else 128):
            invalid_prefix_lengths.append(prefix)
        else:
            d[prefix] = length
    # Build the output string, using 0s and overriding with values that are in the dictionary...
    transformed_value = ''
    # Track the total distribution for all prefix lengths provided...
    total = 0
    for i in range(0, 32 if is_ipv4 else 128):
        if (i + 1) in d:
            transformed_value = transformed_value + str(d[i + 1]) + ' '
            total += d[i + 1]
        else:
            transformed_value = transformed_value + '0 '
    err = None
    if len(invalid_prefix_lengths) > 0:
        err = 'Found invalid prefix lengths: ' + ' '.join([str(a) for a in invalid_prefix_lengths])
    elif total != 100:
        err = 'Total distribution of prefix lengths is ' + str(total) + \
              '; distribution values must add to 100 (%)'
    return transformed_value, err
