from StcIntPythonPL import PLLogger, CHandleRegistry
import json
import spirent.methodology.utils.json_utils as json_utils
from spirent.core.utils.scriptable import AutoCommand
import spirent.cloudstress.cfg_cmd_utils as cfg_cmd_utils
import spirent.cloudstress.result_utils as result_utils
import spirent.cloudstress.cmd_utils as cmd_utils
import spirent.methodology.utils.sql_utils as sql_utils
import spirent.methodology.utils.glimpse_utils as g_utils


PKG = "spirent.methodology"
PKG_CS = "spirent.cloudstress"


def create_session(ctlr):
    session = ctlr.GetObject('CloudStressSession')
    if session:
        return ''

    token = None
    with AutoCommand('CloudStressCreateSessionCommand') as session_cmd:
        session_cmd.Set('ParentRes', ctlr.GetObjectHandle())
        session_cmd.Execute()
        token = session_cmd.Get('SecurityToken')

    if not token:
        return 'Unable to create session.'

    return ''


def connect_to_ctlr_and_create_session(tagname, tagged_objects, params):
    logger = PLLogger.GetLogger('methodology')
    logger.LogDebug('begin connect_to_ctlr_and_create_session custom script')

    err_str, input_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    ctlr_ip = 'localhost'
    if 'ctlr_ip' in input_dict:
        ctlr_ip = input_dict['ctlr_ip']

    tcp_port = 9002
    if 'tcp_port' in input_dict:
        tcp_port = int(input_dict['tcp_port'])

    ctlr = cmd_utils.get_controller()
    if not ctlr or (ctlr and ctlr.Get('HostName') != ctlr_ip):
        if ctlr:
            ctlr.MarkDelete()

        with AutoCommand('ConnectToClusterControllerCommand') as connect_cmd:
            connect_cmd.Set('HostName', ctlr_ip)
            connect_cmd.Set('TcpPort', tcp_port)
            connect_cmd.Execute()
            ctlr = connect_cmd.Get('Ctlr')
            ctlr = CHandleRegistry.Instance().Find(ctlr)

    if not ctlr:
        return 'Unable to connect to controller at: ', ctlr_ip

    err_str = create_session(ctlr)

    logger.LogDebug('end connect_to_ctlr_and_create_session custom script')
    return err_str


def tag_resources(tagname, tagged_objects, params):
    logger = PLLogger.GetLogger('methodology')
    logger.LogDebug('begin tag_resources custom script')

    err_str, input_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    err_str = cfg_cmd_utils.tag_reserved_resources(input_dict)
    logger.LogDebug('end tag_resources custom script')
    return err_str


def get_tdigest_results(tagname, tagged_objects, params):
    instances, err_str = cfg_cmd_utils.get_nodes_and_reserved_instances([], [])[1:]
    if err_str:
        return err_str

    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    model_dict = cfg_cmd_utils.build_model_dict_from_children(instances)
    for statistic in j_dict.get("stat_list", []):
        err_str = result_utils.get_summary_tdigest_results(model_dict.values(),
                                                           statistic)
        if err_str:
            return err_str

    return ''


# Get a list of agents to pull detailed stats from the
# metrics service for.
def get_threshold_res_agent_list(stat):
    query = "SELECT AgentHostname FROM ThresholdResults AS TR, " + \
        "ThresholdResultConfig AS TRC WHERE TRC.Statistic = '" + \
        stat + "' AND TR.ParentHnd = TRC.Handle"

    err_str, res_data = sql_utils.run_sql_on_db_name("LAST_ITERATION", query)
    if err_str:
        return err_str

    row_list = res_data["rows"]
    agent_list = []
    for row in row_list:
        agent_list.append(row[0])
    return agent_list


#    params = {
#        "iteration": "1",
#        "measurement": "cs_agent_memory",  <- InfluxDb table
#        "field_list": ["ops_actual_read_rate"],   <- Column/field
#        "agent_list": ["1.2.3.4", "5.6.7.8"],   <- optional
#        "threshold_stat": "MEMORY_READ_VARIANCE" <- optional
#    }
def get_ms_agent_stats(tagname, tagged_objects, params):
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("params: " + str(params))
    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    for prop in ["iteration", "measurement", "field_list"]:
        if prop not in j_dict.keys():
            return "'" + prop + "' is a required parameter in params"
    iteration = str(j_dict["iteration"])
    measurement = j_dict["measurement"]
    field_list = j_dict["field_list"]
    thr_stat = ""
    agent_list = []
    if "threshold_stat" in j_dict.keys():
        thr_stat = j_dict["threshold_stat"]
    else:
        if "agent_list" in j_dict.keys():
            agent_list = j_dict["agent_list"]
        else:
            agent_list.append("ALL")
    if thr_stat != "":
        agent_list = get_threshold_res_agent_list(thr_stat)

    plLogger.LogDebug("agent_list: " + str(agent_list))
    if not len(agent_list):
        return "No agents."

    # Get the SecurityToken
    token, err_str = cmd_utils.get_session_id()
    if err_str:
        return err_str
    db = "metrics"
    event_table = "CS_AUTODEPLOY_AGENTS_cs_bll_events"

    for agent in agent_list:
        for field in field_list:
            err_str = result_utils.update_ms_agent_summ_stats(
                db, event_table, iteration, token,
                measurement, field, agent)
            if err_str:
                return err_str
    return ""


# The instances should have already been generated
def build_machine_set_map(tagname, tagged_objects, params):
    return result_utils.build_machine_set_map()


# FIXME:
# MOVE THIS ELSEWHERE
def get_inst_and_node_list_from_meta_ids(template_id, node_id):
    # Find the MachineSets
    if template_id == "":
        return "TemplateId must be specified.", [], []

    # Get the machine set map from the SUMMARY DB
    query = "SELECT MachineSetHnd, ResourceId, " + \
        "CloudTemplateInstanceHndList FROM CS_MachineSetInstanceMap"

    err_str, res_data = sql_utils.run_sql_on_db_name("SUMMARY", query)
    if err_str:
        return err_str, [], []

    if "rows" not in res_data or not len(res_data["rows"]):
        return "MachineSet map is empty.", [], []

    row_list = res_data["rows"]
    inst_hnd_list = []
    for row in row_list:
        stored_id = row[1]
        if stored_id == template_id:
            err_str, inst_hnd_list = json_utils.load_json(row[2])
            if err_str:
                return "Failed to load instance list for " + template_id, [], []
            break

    if not len(inst_hnd_list):
        return "Could not find CloudTemplateInstances with TemplateId " + \
            template_id, [], []

    # Get the applicable CloudStressNodes
    node_hnd_list = []
    if node_id != "":
        # inst_hnd_list should have at least one thing in it at this point
        inst = CHandleRegistry.Instance().Find(inst_hnd_list[0])
        ctm = inst.GetParent()
        ctn_list = ctm.GetObjects("CloudTemplateNode")
        for ctn in ctn_list:
            if ctn.Get("ResId") == node_id:
                # There should only be one applicable node per model
                # given a specific node ID (though the same node ID
                # may be in use by different models when agents are
                # discovered by IP)
                node_hnd_list.append(ctn.GetObjectHandle())
                break
    return "", inst_hnd_list, node_hnd_list


# params:
# {
#     "CpuLoad": "1",
#     "TemplateId": "MachineSet_ResourceId",
#     "NodeId": "Node discovery ID; can be empty string"
# }
def config_specific_node_inst_fixed_cpu_load(tagname, tagged_objects, params):
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("params: " + str(params))
    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    for prop in ["CpuLoad", "TemplateId"]:
        if prop not in j_dict:
            return prop + " must be specified in input params"

    err_str, inst_hnd_list, node_hnd_list = \
        get_inst_and_node_list_from_meta_ids(j_dict.get("TemplateId", ""),
                                             j_dict.get("NodeId", ""))
    if err_str != "":
        return err_str

    # Configure the new CPU Load
    with AutoCommand(PKG_CS + ".ConfigCpuLoadParamsCommand") as cmd:
        cmd.SetCollection("InstanceList", inst_hnd_list)
        cmd.SetCollection("NodeList", node_hnd_list)
        cmd.Set("MinCpuLoad", j_dict["CpuLoad"])
        cmd.Set("MaxCpuLoad", j_dict["CpuLoad"])
        cmd.Execute()
        if cmd.Get("PassFailState") != "PASSED":
            return "Failed to configure CPU load: " + cmd.Get("Status")
    return ""


# params:
# {
#     "ReadRate": "1",
#     "WriteRate": "2",
#     "ReadSize": "1",
#     "WriteSize": "2",
#     "BufferSize": "1",
#     "AccessPattern": "RANDOM",
#     "TemplateId": "MachineSet_ResourceId",
#     "NodeId": "Node discovery ID; can be empty string"
# }
def config_specific_node_inst_fixed_mem_load(tagname, tagged_objects, params):
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("params: " + str(params))
    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    for prop in ["ReadRate", "WriteRate", "ReadSize", "WriteSize",
                 "BufferSize", "AccessPattern", "TemplateId"]:
        if prop not in j_dict:
            return prop + " must be specified in input params"

    err_str, inst_hnd_list, node_hnd_list = \
        get_inst_and_node_list_from_meta_ids(j_dict.get("TemplateId", ""),
                                             j_dict.get("NodeId", ""))
    if err_str != "":
        return err_str

    # Configure the new Memory Load
    with AutoCommand(PKG_CS + ".ConfigMemoryLoadParamsCommand") as cmd:
        cmd.SetCollection("InstanceList", inst_hnd_list)
        cmd.SetCollection("NodeList", node_hnd_list)
        cmd.Set("MinReadRate", j_dict["ReadRate"])
        cmd.Set("MaxReadRate", j_dict["ReadRate"])
        cmd.Set("MinWriteRate", j_dict["WriteRate"])
        cmd.Set("MaxWriteRate", j_dict["WriteRate"])
        cmd.Set("ReadSize", j_dict["ReadSize"])
        cmd.Set("WriteSize", j_dict["WriteSize"])
        cmd.Set("BufferSize", j_dict["BufferSize"])
        cmd.Set("AccessPattern", j_dict["AccessPattern"])
        cmd.Execute()
        if cmd.Get("PassFailState") != "PASSED":
            return "Failed to configure Memory load: " + cmd.Get("Status")
    return ""


# params:
# {
#     "ReadRate": "1",
#     "WriteRate": "2",
#     "ReadSize": "1",
#     "WriteSize": "2",
#     "Connections": "2",
#     "Transport": "TCP",
#     "TemplateId": "MachineSet_ResourceId",
#     "NodeId": "Node discovery ID; can be empty string"
# }
def config_specific_node_inst_fixed_net_load(tagname, tagged_objects, params):
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("params: " + str(params))
    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    for prop in ["ReadRate", "WriteRate", "ReadSize", "WriteSize",
                 "Connections", "Transport", "TemplateId"]:
        if prop not in j_dict:
            return prop + " must be specified in input params"

    err_str, inst_hnd_list, node_hnd_list = \
        get_inst_and_node_list_from_meta_ids(j_dict.get("TemplateId", ""),
                                             j_dict.get("NodeId", ""))
    if err_str != "":
        return err_str

    # Configure the new Memory Load
    with AutoCommand(PKG_CS + ".ConfigNetworkLoadParamsCommand") as cmd:
        cmd.SetCollection("InstanceList", inst_hnd_list)
        cmd.SetCollection("NodeList", node_hnd_list)
        cmd.Set("MinReadRate", j_dict["ReadRate"])
        cmd.Set("MaxReadRate", j_dict["ReadRate"])
        cmd.Set("MinWriteRate", j_dict["WriteRate"])
        cmd.Set("MaxWriteRate", j_dict["WriteRate"])
        cmd.Set("ReadSize", j_dict["ReadSize"])
        cmd.Set("WriteSize", j_dict["WriteSize"])
        cmd.Set("Connections", j_dict["Connections"])
        cmd.Set("Transport", j_dict["Transport"])
        cmd.Execute()
        if cmd.Get("PassFailState") != "PASSED":
            return "Failed to configure Network load: " + cmd.Get("Status")
    return ""


# params:
# {
#     "ReadRate": "1",
#     "WriteRate": "2",
#     "ReadSize": "1",
#     "WriteSize": "2",
#     "FileSize": "8",
#     "AccessPattern": "RANDOM",
#     "QueueDepth": "16",
#     "TemplateId": "MachineSet_ResourceId",
#     "NodeId": "Node discovery ID; can be empty string"
# }
def config_specific_node_inst_fixed_stor_load(tagname, tagged_objects, params):
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("params: " + str(params))
    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    for prop in ["ReadRate", "WriteRate", "ReadSize", "WriteSize",
                 "FileSize", "AccessPattern", "QueueDepth",
                 "TemplateId"]:
        if prop not in j_dict:
            return prop + " must be specified in input params"

    err_str, inst_hnd_list, node_hnd_list = \
        get_inst_and_node_list_from_meta_ids(j_dict.get("TemplateId", ""),
                                             j_dict.get("NodeId", ""))
    if err_str != "":
        return err_str

    # Configure the new Memory Load
    with AutoCommand(PKG_CS + ".ConfigStorageLoadParamsCommand") as cmd:
        cmd.SetCollection("InstanceList", inst_hnd_list)
        cmd.SetCollection("NodeList", node_hnd_list)
        cmd.Set("MinReadRate", j_dict["ReadRate"])
        cmd.Set("MaxReadRate", j_dict["ReadRate"])
        cmd.Set("MinWriteRate", j_dict["WriteRate"])
        cmd.Set("MaxWriteRate", j_dict["WriteRate"])
        cmd.Set("ReadSize", j_dict["ReadSize"])
        cmd.Set("WriteSize", j_dict["WriteSize"])
        cmd.Set("FileSize", j_dict["FileSize"])
        cmd.Set("AccessPattern", j_dict["AccessPattern"])
        cmd.Set("QueueDepth", j_dict["QueueDepth"])
        cmd.Execute()
        if cmd.Get("PassFailState") != "PASSED":
            return "Failed to configure Storage load: " + cmd.Get("Status")
    return ""


def disp_dm(tagname, tagged_objects, params):
    result_utils.disp_dm()


#    params = {
#        "iteration": "1",
#        "threshold_stat": "MEMORY_READ_VARIANCE",
#        "tdigest_stat": "MEMORY_READ_RATE" <- optional.
#        If not specified threshold_stat is used for tdigest_stat
#    }
def get_tdigest_agent_stats(tagname, tagged_objects, params):
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("params: " + str(params))
    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    for prop in ["iteration", "threshold_stat"]:
        if prop not in j_dict.keys():
            return "'" + prop + "' is a required parameter in params"

    iteration = str(j_dict["iteration"])
    thr_stat = j_dict.get("threshold_stat")
    tdigest_stat = j_dict.get("tdigest_stat", thr_stat)
    return result_utils.get_tdigest_agent_stats(
        iteration, thr_stat, tdigest_stat)


# Build a map between profiles, templates (models) and nodes to
# indicate which node is using which profile.
def build_profile_map(tagname, tagged_objects, params):
    return result_utils.build_profile_map()


def delete_session(tagname, tagged_objects, params):
    return cmd_utils.delete_session()


# FIXME:
# The handling of the expected deploy count is not quite right
# as the machine set could be deployed multiple times.  However,
# the machine group (tag) may refer to machine sets with different
# expected deploy counts so it may not be possible to pass in a
# single expected deploy count.
# One option is to update the count parameter in the machine set
# whenever instances are to be deployed or torn down (count would
# represent the total number of expected agents after the deployment
# is updated).  Another option is to put this information somewhere
# else (ie another property) as a state-like parameter.
# params: {
#     "machine_set_tag_name": "WestMachineGroup"
# }
def proto_verify_machine_set_deployed_count(tagname, tagged_objects, params):
    plLogger = PLLogger.GetLogger("proto_verify_machine_set_deployed_count")
    plLogger.LogInfo("start")
    plLogger.LogInfo("params: " + json.dumps(params))
    err_str, j_dict = json_utils.load_json(params)
    if err_str:
        return err_str

    if "machine_set_tag_name" not in j_dict:
        plLogger.LogInfo("missing machine_set_tag_name, no machine sets")
        return "Missing machine_set_tag_name in input params."
    ms_list = cmd_utils.get_auto_deploy_machine_sets(
        [], j_dict["machine_set_tag_name"])
    if not len(ms_list):
        plLogger.LogInfo("Did not find any MachineSets that have auto-" +
                         "deployed agents.")
        return ""

    # Dump into a table (result/verdict will be provided by
    # RunSqlCommand)
    # Create the summary table (if not exists)
    sql_ops = []
    table_name = "CS_MachineSetDeployedAgents"
    create_table = "CREATE TABLE IF NOT EXISTS " + \
        table_name + " (ID INTEGER PRIMARY KEY, " + \
        "MachineSetHnd INTEGER, " + \
        "MachineSetName VARCHAR, DeployedCount INTEGER, " + \
        "DeployCount INTEGER)"

    sql_ops = [
        {
            "enable": True,
            "db_information": {"db_name": "LAST_ITERATION"},
            "sql_statement": [{"static": create_table}]
        }
    ]

    insert_table_part = "INSERT INTO " + table_name + " " + \
        "(MachineSetHnd, MachineSetName, DeployedCount, DeployCount) " + \
        "VALUES "

    for ms in ms_list:
        dp = ms.GetObject(PKG + ".stm.MachineSetDeploymentParams")
        if not dp:
            return "Could not find MachineSetDeploymentParams under the " + \
                "MachineSet: " + ms.Get("Name")

        j_str = dp.Get("ParamsJson")
        plLogger.LogDebug("ParamsJson: " + j_str)
        err_str, dp_data = json_utils.load_json(j_str)
        if err_str:
            return "Failed to read MachineSetDeploymentParams JSON: " + \
                err_str
        cred_key = dp_data.get("credential_key", None)
        if cred_key is None:
            return "Failed to find credential_key in deployment JSON"

        # FIXME:
        # Use the input parameter when it is necessary (and provided)
        # exp_count = j_dict.get("expected_count", ms.Get("Count"))

        """
        bll_cmd_key      843_1493174585
        session_id       gYTQWfieR-Wl7tvqjm7Rqw
        machine_set_id   UniqueMachineId
        methodology_key  CS_AUTODEPLOY_AGENTS
        created_by       glimpse
        """

        sess_id, err_str = cmd_utils.get_session_id()
        if err_str:
            return err_str

        inst_meta = {}
        meta_str = dp.Get("DeployedInstanceMetaDataJson")
        if meta_str:
            err_str, inst_meta = json_utils.load_json(meta_str)
            if err_str:
                plLogger.LogWarn("Invalid DeployedInstanceMetaDataJson " +
                                 "found in MachineSet " + ms.Get("Name") +
                                 ": " + str(meta_str))
                inst_meta = {}
        if not inst_meta:
            inst_meta = {
                "session_id": sess_id,
                "methodology_key": "CS_AUTODEPLOY_AGENTS",
                "created_by": "glimpse",
                "machine_set_id": ms.Get("ResourceId")
            }

        opt_dict = {
            "status": "active",
            "user": "true",
            "meta": inst_meta
        }
        err_str, res_list = g_utils.get_resources(
            cred_key, "instances", opt_dict=opt_dict)
        plLogger.LogDebug("res_list: " + json.dumps(res_list))

        insert_table = insert_table_part + "(" + \
            str(ms.GetObjectHandle()) + ", '" + ms.Get("Name") + "', " + \
            str(len(res_list)) + ", " + str(ms.Get("Count")) + ")"

        sql_ops.append(
            {
                "enable": True,
                "db_information": {
                    "db_name": "LAST_ITERATION",
                    "dest_db": {
                        "dest_db_name": "LAST_ITERATION",
                        "dest_table_name": table_name
                    }
                },
                "sql_statement": [{"static": insert_table}]
            }
        )
    sql_op_list = {
        "enable": True,
        "sql_operations": sql_ops
    }
    with AutoCommand(PKG + ".RunSqlCommand") as sql_cmd:
        sql_cmd.Set("DbJsonString", json.dumps(sql_op_list))
        sql_cmd.Execute()
        if sql_cmd.Get("PassFailState") != "PASSED":
            return sql_cmd.Get("Status")

    """
        # Provide a result to affect the verdict
        fail_explanation = "Actual number of deployed instances (" + \
            str(inst_up_count) + ") does not equal the expected number " + \
            "of deployed instances (" + str(exp_count) + ")."
        pass_explanation = "All instances deployed successfully."
        is_pass = False
        verdict_explanation = fail_explanation
        if inst_up_count == exp_count:
            is_pass = True
        verdict_explanation = pass_explanation
        apply_verdict = True
        col_names = ["Machine Set Name",
                     "Expected Deployed Count",
                     "Actual Deployed Count"]
        res_rows = [[ms.Get("Name"), exp_count, inst_up_count]]
        report_group = "SUMMARY"
        disp_name = "Verify Deployed Instances"
        sql_query = "SELECT * FROM FakeTable"

        # Generate and provide results to the results framework
        import spirent.methodology.results.ProviderDataGenerator as prov_gen
        from spirent.methodology.results.ProviderConst \
            import ProviderConst as prov_const
        import traceback

        try:
            res_data = prov_gen.get_table_db_query_data(
                sql_query,
                is_pass,
                verdict_explanation,
                apply_verdict,
                col_names,
                res_rows,
                report_group,
            disp_name,
                pass_explanation,
                fail_explanation)
            prov_gen.submit_provider_data(res_data)
        except:
            stack_trace = traceback.format_exc()
            plLogger.LogError(stack_trace)
            prov_gen.submit_command_execution_error(
                disp_name,
                prov_const.UNKNOWN_EXCEPTION_MESSAGE,
                stack_trace)
    """
    return ""
