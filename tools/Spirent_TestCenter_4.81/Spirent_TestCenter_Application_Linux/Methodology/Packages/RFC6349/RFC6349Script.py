from StcIntPythonPL import *
import json
import re
import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.sql_utils as sql_utils
import spirent.methodology.utils.tag_utils as tag_utils
import spirent.methodology.utils.rt_status_utils as rt_status_utils
import spirent.methodology.utils.dyn_obj_utils as dyn_obj_utils
from spirent.methodology.manager.utils.methodology_manager_utils \
    import MethodologyManagerUtils as mgr_utils


def SetContextTitle(tagname, target, params):
    '''
        Quick means to change the title of the RT status context.
        params - holds the title string
    '''
    rt_status_utils.set_rt_context_status(params.replace('"', ''))
    return ""


def UpdateMtuValues(tagname, target, params):
    sql = '''SELECT PortHandle, MAX(L1Mtu) FROM RFC6349BestMtu GROUP BY PortHandle'''
    err, table_data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    hnd_reg = CHandleRegistry.Instance()
    rs = table_data['rows']
    for row in rs:
        port = hnd_reg.Find(int(row[0]))
        if not port:
            return "Unable to find the port from the port handle."
        phy = port.GetObject("EthernetCopper", RelationType("ActivePhy"))
        if not phy:
            phy = port.GetObject("EthernetFiber", RelationType("ActivePhy"))
        if not phy:
            return "Failed to identify a port phy for the TCP server."
        phy.Set("Mtu", int(row[1]))
    return ""


def InitRtMtuChart(tagname, target, params):
    '''
        This function will essentially do the work of the InitRealTimeResultsCommand,
        but for creating a column type chart.

        UpdateRealTimeResultsCommand will complain once about ResultInfoJson not
        having a valid result_id value. After this StmRtResult is removed, the RT
        framework will continue to work fine for subsequent sub tests.
    '''
    display = '''[
        {
            "source_type": "SUMMARY_DB",
            "definition": {
                "series": [],
                "title": {"text": "MTU Test"},
                "chart": {"type": "column"},
                "xAxis": {
                    "categories": ["Server Tx", "Client Tx"],
                    "title": {"text": "Connections"}
                },
                "yAxis": [
                    {
                        "min": 0,
                        "max": 1600,
                        "title": {"text": "Transmitted Frame Size (Bytes)"}
                    }
                ]
            },
            "result_id": "RFC6349RTMtuBChart",
            "type": "chart"
        }
    ]
    '''
    err, display_dict = json_utils.load_json(display)
    if err:
        return err

    sql = '''SELECT `Connection Name` FROM RFC6349ConnectionConfig'''
    err, table_data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    rs = table_data['rows']
    s = []
    for row in rs:
        s.append({'name': row[0]})

    display_dict[0]['definition']['series'] = s
    display = json.dumps(display_dict)
    ctor = CScriptableCreator()
    stm_rt_result = ctor.Create('StmRtResult', mgr_utils.get_meth_manager())
    stm_rt_result.Set('ResultDisplayJson', display)
    stm_rt_result.Set('ResultInfoJson', '[{}]')
    tag_utils.add_tag_to_object(stm_rt_result, 'tMtuRtResults')
    return ""


def UpdateRtMtuChart(tagname, target, params):
    # Reference the STM real time results object...
    stm_rt_result_list = tag_utils.get_tagged_objects_from_string_names(['tMtuRtResults'])
    if not isinstance(stm_rt_result_list, list) or len(stm_rt_result_list) == 0:
        return "Could not find the MTU real time result object."
    stm_rt_result = stm_rt_result_list[0]

    # Get the frame size for the current iteration...
    frame_size = int(params)

    server_sbs = tag_utils.get_tagged_objects_from_string_names(["mtu_server_ttStreamBlock"])
    client_sbs = tag_utils.get_tagged_objects_from_string_names(["mtu_client_ttStreamBlock"])

    series = []

    sql = '''SELECT `Connection Name` FROM RFC6349ConnectionConfig'''
    err, table_data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    for i, (ssb, csb, row) in enumerate(zip(server_sbs, client_sbs, table_data['rows'])):
        result = ssb.GetObject("RxStreamSummaryResults")
        s = frame_size if result.Get("SigFrameRate") > 0 else 0
        result = csb.GetObject("RxStreamSummaryResults")
        c = frame_size if result.Get("SigFrameRate") > 0 else 0
        series.append({'name': row[0], 'data': [[0, s], [1, c]]})

    # Form the ResultDataJson...
    chart_data = {}
    chart_data['result_id'] = 'RFC6349RTMtuBChart'
    chart_data['type'] = 'chart'
    chart_data['data'] = {'series': series}
    data = json.dumps([chart_data])

    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("UpdateRtMtuChart::ResultDataJson: " + data)

    stm_rt_result.Set('ResultDataJson', data)
    return ""


def InitRtBbChart(tagname, target, params):
    '''
        This function will essentially do the work of the InitRealTimeResultsCommand,
        but for creating a column type chart.

        UpdateRealTimeResultsCommand will complain once about ResultInfoJson not
        having a valid result_id value. After this StmRtResult is removed, the RT
        framework will continue to work fine for subsequent sub tests.
    '''
    display = '''[
        {
            "source_type": "SUMMARY_DB",
            "definition": {
                "series": [],
                "title": {"text": "Bandwidth Bottleneck Test"},
                "chart": {"type": "column"},
                "xAxis": {
                    "categories": ["Server Tx", "Client Tx"],
                    "title": {"text": "Connections"}
                },
                "yAxis": [{"min": 0, "title": {"text": "Transmitted Throughput (Mbps)"}}]
            },
            "result_id": "RFC6349RTBbBChart",
            "type": "chart"
        }
    ]
    '''
    err, display_dict = json_utils.load_json(display)
    if err:
        return err

    sql = '''SELECT `Connection Name` FROM RFC6349ConnectionConfig'''
    err, table_data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    rs = table_data['rows']
    s = []
    for row in rs:
        s.append({'name': row[0]})

    display_dict[0]['definition']['series'] = s
    display = json.dumps(display_dict)
    ctor = CScriptableCreator()
    stm_rt_result = ctor.Create('StmRtResult', mgr_utils.get_meth_manager())
    stm_rt_result.Set('ResultDisplayJson', display)
    stm_rt_result.Set('ResultInfoJson', '[{}]')
    tag_utils.add_tag_to_object(stm_rt_result, 'tBbRtResults')
    return ""


def UpdateRtBbChart(tagname, target, params):
    # Reference the STM real time results object...
    stm_rt_result_list = tag_utils.get_tagged_objects_from_string_names(['tBbRtResults'])
    if not isinstance(stm_rt_result_list, list) or len(stm_rt_result_list) == 0:
        return "Could not find the BB real time result object."
    stm_rt_result = stm_rt_result_list[0]

    # Get the frame size for the current iteration...
    # load = int(params)

    server_sbs = tag_utils.get_tagged_objects_from_string_names(["bb_server_ttStreamBlock"])
    client_sbs = tag_utils.get_tagged_objects_from_string_names(["bb_client_ttStreamBlock"])

    series = []

    sql = '''SELECT `Connection Name` FROM RFC6349ConnectionConfig'''
    err, table_data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    sql = '''CREATE TABLE IF NOT EXISTS RFC6349BestBb
            (ConnectionIndex, Tag, PortHandle, DroppedFrames, L1BitRate)'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    for i, (ssb, csb, row) in enumerate(zip(server_sbs, client_sbs, table_data['rows'])):
        port = ssb.GetParent()
        if not port:
            return "Could not find port for stream block"
        port_handle = port.Get("Handle")
        tag = '''bb_server_ttStreamBlock'''
        results = ssb.GetObject("RxStreamSummaryResults")
        if not results:
            return "Could not find results for stream block"
        dropped = results.Get("DroppedFrameCount")
        port_cfg = port.GetObject("Generator").GetObject("GeneratorConfig")
        if not port_cfg:
            return "Could not find generator config for stream block's port"
        rate = port_cfg.Get("BpsLoad") if results.Get("FrameRate") > 0 else 0
        s = rate if dropped == 0 else 0

        sql = '''INSERT INTO RFC6349BestBb VALUES ({0}, '{1}', {2}, {3}, {4})
            '''.format(i, tag, port_handle, dropped, rate)
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err

        port = csb.GetParent()
        if not port:
            return "Could not find port for stream block"
        port_handle = port.Get("Handle")
        tag = '''bb_client_ttStreamBlock'''
        results = csb.GetObject("RxStreamSummaryResults")
        if not results:
            return "Could not find results for stream block"
        dropped = results.Get("DroppedFrameCount")
        port_cfg = port.GetObject("Generator").GetObject("GeneratorConfig")
        if not port_cfg:
            return "Could not find generator config for stream block's port"
        rate = port_cfg.Get("BpsLoad") if results.Get("FrameRate") > 0 else 0
        c = rate if dropped == 0 else 0

        sql = '''INSERT INTO RFC6349BestBb VALUES ({0}, '{1}', {2}, {3}, {4})
            '''.format(i, tag, port_handle, dropped, rate)
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err

        series.append({'name': row[0], 'data': [[0, s * 1e-6], [1, c * 1e-6]]})

    # Form the ResultDataJson...
    chart_data = {}
    chart_data['result_id'] = 'RFC6349RTBbBChart'
    chart_data['type'] = 'chart'
    chart_data['data'] = {'series': series}
    data = json.dumps([chart_data])

    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("RFC6349RTBbBChart::ResultDataJson: " + data)

    stm_rt_result.Set('ResultDataJson', data)
    return ""


def RttRtGraph(tagname, target, params):
    json_str = target[0].Get("InputJson")
    err, input_dict = json_utils.load_json(json_str)
    if err:
        return err

    sql = '''SELECT `Connection Name` FROM RFC6349ConnectionConfig'''
    err, table_data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    series = []
    rs = table_data['rows']
    for row in rs:
        series.append({"name": row[0]})
    input_dict[0]['definition']['series'] = series
    target[0].Set("InputJson", json.dumps(input_dict))
    return ""


def WriteRFC6349PhyInfo(tagname, target, params):
    sql = '''CREATE TABLE IF NOT EXISTS RFC6349PhyInfo
            (
                ConnectionIndex,
                Type,
                Handle,
                PortHandle,
                PhyHandle,
                LineSpeed,
                L1Mtu
            )'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err
    sql = ''' SELECT 18 + `Server VLAN Enable` * 4 + `Server Inner VLAN Enable` * 4
              FROM RFC6349ConnectionConfig'''
    err, server_eths = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err
    sql = ''' SELECT 18 + `Client VLAN Enable` * 4 + `Client Inner VLAN Enable` * 4
              FROM RFC6349ConnectionConfig'''
    err, client_eths = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    servers = tag_utils.get_tagged_objects_from_string_names(["tcpraw_server_ttEmulatedDevice"])
    for index, server in enumerate(servers):
        port = server.GetObject("Port", RelationType("AffiliationPort"))
        if not port:
            return "Failed to identify the port for the TCP server."
        phy = port.GetObject("EthernetCopper", RelationType("ActivePhy"))
        if not phy:
            phy = port.GetObject("EthernetFiber", RelationType("ActivePhy"))
        if not phy:
            return "Failed to identify a port phy for the TCP server."
        err, line_speed = get_line_speed(phy.Get("LineSpeed"))
        if err:
            return err
        # Update the Phy's MTU based upon the VLANs used...
        mtu = phy.Get("Mtu") - server_eths['rows'][index][0]
        phy.Set("Mtu", mtu)
        sql = "INSERT INTO RFC6349PhyInfo VALUES ({0}, '{1}', {2}, {3}, {4}, {5}, {6})".format(
            index,
            "server",
            server.Get("Handle"),
            port.Get("Handle"),
            phy.Get("Handle"),
            line_speed,
            mtu)
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err

    clients = tag_utils.get_tagged_objects_from_string_names(["tcpraw_client_ttEmulatedDevice"])
    for index, client in enumerate(clients):
        port = client.GetObject("Port", RelationType("AffiliationPort"))
        if not port:
            return "Failed to identify the port for the TCP client."
        phy = port.GetObject("EthernetCopper", RelationType("ActivePhy"))
        if not phy:
            phy = port.GetObject("EthernetFiber", RelationType("ActivePhy"))
        if not phy:
            return "Failed to identify a port phy for the TCP client."
        err, line_speed = get_line_speed(phy.Get("LineSpeed"))
        if err:
            return err
        # Update the Phy's MTU based upon the VLANs used...
        mtu = phy.Get("Mtu") - client_eths['rows'][index][0]
        phy.Set("Mtu", mtu)
        sql = "INSERT INTO RFC6349PhyInfo VALUES ({0}, '{1}', {2}, {3}, {4}, {5}, {6})".format(
            index,
            "client",
            client.Get("Handle"),
            port.Get("Handle"),
            phy.Get("Handle"),
            line_speed,
            mtu)
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err

    sql = '''CREATE TABLE RFC6349TputValues AS
        SELECT
        phy.ConnectionIndex AS 'ConnectionIndex',
        c.`Connection Name` AS 'Connection Name',
        MAX(CAST(mtu.L1Mtu AS INT)) AS 'L1Mtu',
        18 + c.`Server VLAN Enable` * 4 + c.`Server Inner VLAN Enable` * 4 AS 'EthBytes',
        phy.LineSpeed AS 'LineSpeed'
        FROM RFC6349PhyInfo AS phy
        JOIN RFC6349ConnectionConfig AS c ON c.rowid = phy.ConnectionIndex + 1
        JOIN  RFC6349BestMtu   AS mtu ON mtu.PortHandle = phy.PortHandle
        WHERE phy.Type = 'server'
        GROUP BY phy.ConnectionIndex'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err
    return ""


def get_line_speed(s):
    s = str(s)
    if s.lower() == 'speed_100m':
        return "", 100000000
    if s.lower() == 'speed_1g':
        return "", 1000000000
    if s.lower() == 'speed_10g':
        return "", 10000000000
    if s.lower() == 'speed_40g':
        return "", 40000000000
    return "Unrecognized line speed: " + s, 0


def WriteRFC6349RWndTable(tagname, target, params):
    sql = '''CREATE TABLE RFC6349RWndMax
            (
                ConnectionIndex,
                ClientHandle,
                ClientRxWindowSizeLimit,
                ServerHandle,
                ServerRxWindowSizeLimit,
                MaxRxWindowSizeLimit
            )'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    sql = '''CREATE TABLE RFC6349RWndMaxAudit
            (
                Iteration,
                ConnectionIndex,
                ClientHandle,
                ClientRxWindowSizeLimit,
                ServerHandle,
                ServerRxWindowSizeLimit
            )'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    clients = tag_utils.get_tagged_objects_from_string_names(["tcpraw_profiles_ttClientProfile"])
    servers = tag_utils.get_tagged_objects_from_string_names(["tcpraw_profiles_ttServerProfile"])
    for index, (client, server) in enumerate(zip(clients, servers)):
        srwnd = server.Get("RxWindowSizeLimit")
        crwnd = client.Get("RxWindowSizeLimit")
        mrwnd = max(srwnd, crwnd)
        sql = "INSERT INTO RFC6349RWndMax VALUES ({0}, {1}, {2}, {3}, {4}, {5})".format(
            index, server.Get("Handle"), srwnd, client.Get("Handle"), crwnd, mrwnd)
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err
    return ""


def UpdateFromRFC6349RWndTable(tagname, target, params):
    plLogger = PLLogger.GetLogger("methodology")
    hnd_reg = CHandleRegistry.Instance()
    fraction = float(target[0].Get("CurrVal"))
    iteration = int(target[0].Get("Iteration"))
    plLogger.LogDebug("UpdateFromRFC6349RWndTable fraction: " + str(fraction))

    err, data = sql_utils.run_sql_on_db_name("SUMMARY", "SELECT * FROM RFC6349RWndMax")
    if err:
        return err

    for row in data.get("rows", []):
        server_handle = int(row[1])
        client_handle = int(row[3])
        wnd_size = int(int(row[5]) * fraction)
        wnd_size = 1000000 if wnd_size == 0 else wnd_size

        client = hnd_reg.Find(client_handle)
        if not client:
            return "Could not find client with handle " + str(client_handle)
        server = hnd_reg.Find(server_handle)
        if not server:
            return "Could not find server with handle " + str(server_handle)

        client.Set("RxWindowSizeLimit", wnd_size)
        server.Set("RxWindowSizeLimit", wnd_size)

        sql = "INSERT INTO RFC6349RWndMaxAudit VALUES ({0}, {1}, {2}, {3}, {4}, {5})".format(
            iteration, row[0], row[1], wnd_size, row[3], wnd_size)
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err
    return ""


def GetRetransmissionByteCounts(tagname, target, params):
    '''
        This function will use genericexecution command to fetch the retransmitted
        TCP Payload byte count from the TCP stack. There is one stack per cookie.
        If multiple ports per cookie are used, then the stats will reflect the
        aggregate count for all ports for that cookie.

        It is intended that the virtual ports will each have their own cookie.

        tagname holds the tag name of the port(s) to be processed.
        target holds the port(s) to be processed.
        params holds information to store with the retransmit byte count. It is expected
        that this parameter will be something like an iteration value to use as a secondary
        key within queries.

        The results will be stored in the summary db table RFC6349RetransmitByteCount.
        The table will include port handle, tagname, params, and retransmitbytecount.
    '''
    plLogger = PLLogger.GetLogger("methodology")
    plLogger.LogDebug("GetRetransmissionByteCounts")

    # Collect the retransmit counts...
    if isinstance(target, int):
        target = [target]
    port_handles = [t.Get('Handle') for t in target]
    ctor = CScriptableCreator()
    cmd = ctor.CreateCommand('genericexecution')
    cmd.SetCollection("PortList", port_handles)
    cmd.Set("cmd", "bsdnet netstat -s")
    cmd.Execute()
    cmd.MarkDelete()
    # Parse the linux response strings
    output_list = cmd.GetCollection("OutputList")
    plLogger.LogDebug("OutputList::" + str(output_list))
    retrans_list = re.findall('\(([0-9]*).* retransmitted', "".join(output_list))
    plLogger.LogDebug("retrans_list::" + str(retrans_list))

    if len(retrans_list) != len(port_handles):
        return "Failed to acquire all of the retransmission stats."

    # Store the results that were fetched from the IL...
    sql = '''CREATE TABLE IF NOT EXISTS RFC6349RetransmitByteCount
            (PortHandle, TagName, Secondary, RetransmitByteCount)'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    for port_handle, retr in zip(port_handles, retrans_list):

        sql = ''' SELECT SUM(RetransmitByteCount) FROM RFC6349RetransmitByteCount
                  WHERE PortHandle = {0}'''.format(port_handle)
        err, table_data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err
        last_count = table_data['rows'][0][0]
        if last_count is None:
            last_count = 0

        plLogger.LogDebug("port handle and retr::" + str(port_handle) + " " + str(retr))
        sql = '''INSERT INTO RFC6349RetransmitByteCount VALUES ({0}, '{1}', '{2}', {3})
            '''.format(port_handle, tagname, params, int(retr) - int(last_count))
        plLogger.LogDebug("                 SQL::" + sql)
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err
    return ""


def TputRtGraph(tagname, target, params):
    '''
        tagname represents the tag to the InitRealTimeResultsCommand to be configured.
        target represents the InitRealTimeResultsCommand to be configured.
        params is not used.

        tcpraw_client_ttEmulatedDevice is used to find all RAW TCP clients.
        It is assumed that each client is the only device on its port.
    '''
    json_str = target[0].Get("InputJson")
    err, input_dict = json_utils.load_json(json_str)
    if err:
        return err

    sql = '''CREATE TABLE RFC6349ClientAnResults
            (
                ConnectionIndex,
                ConnectionName,
                TagConnection,
                ClientResultsHandle,
                AnResultsHandle
            )'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    series = []
    subscribe = []
    results_list = []
    devices = tag_utils.get_tagged_objects_from_string_names(["tcpraw_client_ttEmulatedDevice"])
    for n, device in enumerate(devices):
        port = device.GetObject("Port", RelationType("AffiliationPort"))
        if not port:
            return "Failed to identify the port for the TCP client."
        an = port.GetObject("Analyzer")
        if not an:
            return "Failed to find the port Analyzer for the TCP client."
        client = device.GetObject("RawTcpClientProtocolConfig")
        if not client:
            return "Failed to find the TCP client for the tagged device."
        client_result = client.GetObject("RawTcpClientResults")
        if not client_result:
            return "Failed to find the TCP client results for the TCP client."

        name = device.Get("Name")

        # Tag the client for the RT subscribe below...
        tag_client = 'obj_handle_' + str(client.Get("Handle"))
        tag_utils.add_tag_to_object(client, tag_client)
        tag_device = 'obj_handle_' + str(device.Get("Handle"))
        tag_utils.add_tag_to_object(device, tag_device)

        # Tag the client result object with both generic and unique tag names...
        tag_client_results = 'obj_handle_' + str(client_result.Get("Handle"))
        tag_utils.add_tag_to_object(client_result, tag_client_results)
        tag_utils.add_tag_to_object(client_result, "tag_client_result")
        # Tag both result objects with the name of the connection...
        tag_connection = "tag_connection_" + str(n)
        tag_utils.add_tag_to_object(an, tag_connection)
        tag_utils.add_tag_to_object(client_result, tag_connection)

        series.append({"name": name, "data": [[0, 0]]})
        subscribe.append({
                         "config_type": "RawTcpClientProtocolConfig",
                         "result_type": "RawTcpClientResults",
                         "view_attribute_list": ["GoodputRxBps"],
                         "result_parent_tags": [tag_device],
                         "legend": [str(n)],
                         "prefix_port_location": "NONE",
                         "factor": "1e-6"
                         })

        results_list.append({
                            "index": n,
                            "name": name,
                            "tag_connection": tag_connection,
                            "client_result_handle": client_result.Get("Handle"),
                            "an_handle": an.Get("Handle")
                            })

        sql = "INSERT INTO RFC6349ClientAnResults VALUES ({0}, '{1}', '{2}', {3}, {4})".format(
            n,
            name,
            tag_connection,
            client_result.Get("Handle"),
            an.Get("Handle"))
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err

    input_dict[0]['definition']['series'] = series
    input_dict[0]['subscribe'] = subscribe
    target[0].Set("InputJson", json.dumps(input_dict))
    dyn_obj_utils.set_variable("RawTcpClientResultsList", results_list)

    sql = '''CREATE TABLE RFC6349ServerGenResults
            (
                ConnectionIndex,
                ConnectionName,
                TagConnection,
                ServerResultsHandle,
                GenResultsHandle
            )'''
    err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
    if err:
        return err

    devices = tag_utils.get_tagged_objects_from_string_names(["tcpraw_server_ttEmulatedDevice"])
    for n, device in enumerate(devices):
        port = device.GetObject("Port", RelationType("AffiliationPort"))
        if not port:
            return "Failed to identify the port for the TCP server."
        gen = port.GetObject("Generator")
        if not gen:
            return "Failed to find the port generator for the TCP server."
        server = device.GetObject("RawTcpServerProtocolConfig")
        if not server:
            return "Failed to find the TCP server for the tagged device."
        server_result = server.GetObject("RawTcpServerResults")
        if not server_result:
            return "Failed to find the TCP server results for the TCP server."

        name = device.Get("Name")

        # Tag the server ports with a common tag...
        tag_utils.add_tag_to_object(port, 'tcpraw_server_port')

        # Tag the server result object with both generic and unique tag names...
        tag_server_results = 'obj_handle_' + str(server_result.Get("Handle"))
        tag_utils.add_tag_to_object(server_result, tag_server_results)
        tag_utils.add_tag_to_object(server_result, "tag_server_result")
        # Tag both result objects with the name of the connection...
        tag_connection = "tag_connection_" + str(n)
        tag_utils.add_tag_to_object(gen, tag_connection)
        tag_utils.add_tag_to_object(server_result, tag_connection)

        sql = "INSERT INTO RFC6349ServerGenResults VALUES ({0}, '{1}', '{2}', {3}, {4})".format(
            n,
            name,
            tag_connection,
            server_result.Get("Handle"),
            gen.Get("Handle"))
        err, data = sql_utils.run_sql_on_db_name("SUMMARY", sql)
        if err:
            return err
    return ""
