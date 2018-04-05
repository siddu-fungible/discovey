from StcIntPythonPL import *
import fractions
import json
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.tag_utils as tag_utils


PKG = "spirent.methodology"


def set_ebs_color_aware_schedule(tag_name, b, params):
    logger = PLLogger.GetLogger('methodology')
    target_cmd_class = PKG + '.CreateTemplateConfigCommand'
    cmd_list = \
        tag_utils.get_tagged_objects_from_string_names(tag_name,
                                                       class_name=target_cmd_class)
    if len(cmd_list) < 1:
        return "No commands tagged of type {}".format(target_cmd_class)

    err_str, j_dict = json_utils.load_json(params)
    if err_str != '':
        return "Failed parsing input: {}".format(err_str)
    if not j_dict.get('enable', True):
        return ""
    values = j_dict.get('values')
    if isinstance(values, list):
        values = values[0]
    if not values:
        return "Failed to find value dictionary"
    if set(values.keys()) != set(['CBS', 'EBS', 'FrameSize',
                                  'CirFpsLoad', 'EirFpsLoad']):
        return "Value dictionary missing expected list of keys: {}".format(values)
    size = int(values['FrameSize'])
    cbs_frame = int(values['CBS']) / size
    if int(values['CBS']) % size > 0:
        cbs_frame += 1
    ebs_frame = int(values['EBS']) / size
    if int(values['EBS']) % size > 0:
        ebs_frame += 1
    cir_load = float(values['CirFpsLoad'])
    eir_load = float(values['EirFpsLoad'])
    sum_load = cir_load + eir_load
    gcd = fractions.gcd(cir_load, eir_load)
    green_burst = int(cir_load / gcd)
    yellow_burst = int(eir_load / gcd)
    total_burst = green_burst + yellow_burst
    loop_total = (cbs_frame + ebs_frame) * 9 / total_burst
    if (9 * cbs_frame + ebs_frame) % total_burst > 0:
        loop_total += 1
    logger.LogDebug("Parameters: cbs_frame: {}, "
                    "ebs_frame: {}, green: {}, yellow: {}, loops: {}"
                    .format(cbs_frame, ebs_frame, green_burst, yellow_burst,
                            loop_total))
    sched = \
        {
            "baseTemplateFile": "manual-sched-tmpl.xml",
            "modifyList": [
                {
                    "description": "Manual Schedule",
                    "enable": True,
                    "operationList": [
                        {
                            "addObject": {
                                "className": "ManualScheduleEntry",
                                "parentTagName": "ttManualSchedule",
                                "propertyValueList": {
                                    "BurstCount": str(green_burst),
                                    "BurstSize": "1",
                                    "InterBurstGap": str(sum_load),
                                    "InterBurstGapUnit": "FRAMES_PER_SECOND",
                                    "InterEntryGap": str(sum_load),
                                    "InterEntryGapUnit": "FRAMES_PER_SECOND",
                                    "InterFrameGap": str(sum_load),
                                    "InterFrameGapUnit": "FRAMES_PER_SECOND",
                                    "LoopCount": "0"
                                },
                                "tagName": "ttNormalScheduleGreen"
                            }
                        },
                        {
                            "addObject": {
                                "className": "ManualScheduleEntry",
                                "parentTagName": "ttManualSchedule",
                                "propertyValueList": {
                                    "BurstCount": str(yellow_burst),
                                    "BurstSize": "1",
                                    "InterBurstGap": str(sum_load),
                                    "InterBurstGapUnit": "FRAMES_PER_SECOND",
                                    "InterEntryGap": str(sum_load),
                                    "InterEntryGapUnit": "FRAMES_PER_SECOND",
                                    "InterFrameGap": str(sum_load),
                                    "InterFrameGapUnit": "FRAMES_PER_SECOND",
                                    "LoopCount": str(loop_total)
                                },
                                "tagName": "ttNormalScheduleYellow"
                            }
                        },
                        {
                            "addObject": {
                                "className": "ManualScheduleEntry",
                                "parentTagName": "ttManualSchedule",
                                "propertyValueList": {
                                    "BurstCount": "1",
                                    "BurstSize": str(cbs_frame),
                                    "InterBurstGap": "12",
                                    "InterBurstGapUnit": "BYTES",
                                    "InterEntryGap": "12",
                                    "InterEntryGapUnit": "BYTES",
                                    "InterFrameGap": "12",
                                    "InterFrameGapUnit": "BYTES",
                                    "LoopCount": "0"
                                },
                                "tagName": "ttBurstScheduleGreen"
                            }
                        },
                        {
                            "addObject": {
                                "className": "ManualScheduleEntry",
                                "parentTagName": "ttManualSchedule",
                                "propertyValueList": {
                                    "BurstCount": "1",
                                    "BurstSize": str(ebs_frame),
                                    "InterBurstGap": "12",
                                    "InterBurstGapUnit": "BYTES",
                                    "InterEntryGap": "12",
                                    "InterEntryGapUnit": "BYTES",
                                    "InterFrameGap": "12",
                                    "InterFrameGapUnit": "BYTES",
                                    "LoopCount": "1"
                                },
                                "tagName": "ttBurstScheduleYellow"
                            }
                        },
                        {
                            "relation": {
                                "relationType": "LoopBackToEntry",
                                "sourceTag": "ttNormalScheduleYellow",
                                "targetTag": "ttNormalScheduleGreen"
                            }
                        }
                    ]
                }
            ]
        }

    for cmd in cmd_list:
        cmd.Set('InputJson', json.dumps(sched))
    return ""
