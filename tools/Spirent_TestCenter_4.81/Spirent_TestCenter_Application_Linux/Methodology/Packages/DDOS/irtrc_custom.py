from StcIntPythonPL import *

import json
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.data_model_utils as dm_utils


def initialize_irtrc_list_and_final_irtrc_json(TagName, TaggedObjs, Params):
    '''
    Param ignored
    '''

    # TagName ignored
    # TaggedObjs ignored

    # init Attack IRTRC
    attack_dict = []
    err, obj_list = dm_utils.get_class_objects(
        [], ["Attack_IRTRC"],
        "spirent.methodology.InitRealTimeResultsCommand", enable_recur_search=False)
    if err != "":
        err = "Failed to get bll object"
        return err

    for obj in obj_list:
        obj.Set("InputJson", json.dumps(attack_dict))

    # init Finalize IRTRC
    finalize_dict = [{
        "definition": {
            "subtitle": {
                "text": "Attack Rate over Time"
            },
            "yAxis": {
                "minPadding": 0.2,
                "maxPadding": 0.2,
                "title": {
                    "text": "Tx Rate (Bps)"
                }
            },
            "title": {
                "text": "Attack Rate"
            },
            "chart": {
                "type": "line"
            },
            "tooltip": {
                "headerFormat": "<span style=\"font-size: 10px\">{point.key}s</span><br/>"
            },
            "plotOptions": {
                "series": {
                    "lineWidth": 1
                }
            },
            "xAxis": {
                "minPadding": 0.2,
                "gridLineWidth": 1,
                "title": {
                    "text": "Time (s)"
                },
                "maxPadding": 0.2
            },
            "legend": {
                "enabled": True
            },
            "series": []
        },
        "run_sql": [
            {
                "enable": True,
                "sql_operations": [
                    {
                        "sql_statement": [
                            {
                                "static": ("CREATE TABLE IF NOT EXISTS DdosAttackThroughputStats "
                                           "AS SELECT (SELECT timestamp FROM GoodputAggPortStats "
                                           "WHERE ROWID=1)AS timestamp")
                            }
                        ],
                        "db_information": {
                            "db_name": "SUMMARY"
                        }
                    },
                    {
                        "temp_table_name": "DdosAttackThroughputStats",
                        "sql_statement": [],
                        "db_information": {
                            "db_name": "SUMMARY"
                        }
                    }
                ]
            }
        ],
        "source_type": "SUMMARY_DB",
        "query": {
            "data_column_names": [
                "timestamp"
            ],
            "timestamp_column_name": "timestamp",
            "table": "DdosAttackThroughputStats"
        },
        "type": "chart",
        "result_id": "DdosAttackChartData"
    }]
    err, obj_list = dm_utils.get_class_objects(
        [], ["Finalize_IRTRC"],
        "spirent.methodology.InitRealTimeResultsCommand", enable_recur_search=False)
    if err != "":
        err = "Failed to get bll object"
        return err

    for obj in obj_list:
        obj.Set("InputJson", json.dumps(finalize_dict))

    return err


def append_to_irtrc_list_and_final_irtrc_json(TagName, TaggedObjs, Params):
    '''
    Param ignored
    '''

    ResultId = TagName + "Stats"
    d = {
        "enable": True,
        "result_id": ResultId,
        "type": "table",
        "source_type": "DATA",
        "definition":
        {
            "headers": [],
            "rows": []
        },
        "subscribe": [
            {
                "result_parent_tags": [TagName],
                "config_type": "StreamBlock",
                "result_type": "TxStreamResults",
                "view_attribute_list": ["OctetRate"],
                "interval": "1"
            }
        ]
    }
    # err, d = json_utils.load_json(Params)
    # if err != '':
    #    return err

    # TagName contains StreamBlock tag to add to IRTRC entries
    # TaggedObjs ignored

    # Append the data subscription to the attack IRTRC
    err, obj_list = dm_utils.get_class_objects(
        [], ["Attack_IRTRC"],
        "spirent.methodology.InitRealTimeResultsCommand", enable_recur_search=False)
    if err != "":
        err = "Failed to get bll object"
        return err

    for obj in obj_list:
        val = obj.Get("InputJson")
        err, j_val = json_utils.load_json(val)
        if err:
            return "Failed to get_json_val_from_string: " + val
        j_val.append(d)
        obj.Set("InputJson", json.dumps(j_val))

    # Modify the chart query and sql in the final IRTRC
    err, sb_list = dm_utils.get_class_objects(
        [], [TagName], "StreamBlock", enable_recur_search=False)
    if err != "":
        err = "Failed to get bll StreamBlock object"
        return err
    # TagName *must* contain an underscore
    sb_name = TagName.split("_")[0] + " " + sb_list[0].Get("Name")

    err, obj_list = dm_utils.get_class_objects(
        [], ["Finalize_IRTRC"],
        "spirent.methodology.InitRealTimeResultsCommand", enable_recur_search=False)
    if err != "":
        err = "Failed to get bll object"
        return err

    for obj in obj_list:
        val = obj.Get("InputJson")
        err, j_val = json_utils.load_json(val)
        if err:
            return "Failed to get_json_val_from_string: " + val
        statement_count = len(j_val[0]["run_sql"][0]["sql_operations"][1]["sql_statement"])
        entry_string = ""
        if statement_count == 0:
            entry_string = ("SELECT (SELECT Timestamp FROM _TABLE_NAME_ WHERE Timestamp = "
                            "(SELECT MAX(Timestamp) FROM _TABLE_NAME_)) as timestamp,"
                            "(SELECT SUM(Data)/8 FROM _TABLE_NAME_ WHERE Timestamp = "
                            "(SELECT MAX(Timestamp) FROM _TABLE_NAME_)) as `_SB_NAME_`")
        else:
            entry_string = (", (SELECT SUM(Data)/8 FROM _TABLE_NAME_ WHERE Timestamp = "
                            "(SELECT MAX(Timestamp) FROM _TABLE_NAME_)) as `_SB_NAME_`")
        entry_string = entry_string.replace("_TABLE_NAME_", ResultId).replace("_SB_NAME_", sb_name)
        d = {"static": entry_string}
        j_val[0]["run_sql"][0]["sql_operations"][1]["sql_statement"].append(d)
        j_val[0]["query"]["data_column_names"].append(sb_name)
        # also populate the CREATE TABLE IF NOT EXISTS query for the initial value
        init_entry_string = ", NULL AS `" + sb_name + "`"
        d = {"static": init_entry_string}
        j_val[0]["run_sql"][0]["sql_operations"][0]["sql_statement"].append(d)
        obj.Set("InputJson", json.dumps(j_val))

    return err
