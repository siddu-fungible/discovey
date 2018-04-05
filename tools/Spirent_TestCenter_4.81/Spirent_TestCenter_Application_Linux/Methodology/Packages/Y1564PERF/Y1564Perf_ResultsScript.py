from StcIntPythonPL import *
import spirent.methodology.utils.tag_utils as tag_utils


PKG = "spirent.methodology"
OBJ_KEY = 'spirent.methodology.Y1564_SvcCfgRamp'


def y1564ResultsReport(tagname, b, params):
    plLogger = PLLogger.GetLogger("Methodology")
    plLogger.LogDebug("Running custom y1564ResultsReport script...")
    if not CObjectRefStore.Exists(OBJ_KEY):
        plLogger.LogWarn('Y1564SvcCfgRampCommand was not called. ' +
                         'Using default threshold values.')
        exp_pktloss = 0
        exp_avgjitter = 0.05
        exp_maxjitter = 0.2
        exp_avglatency = 0.7
        exp_maxlatency = 1.0
        exp_maxoop = 0
        exp_maxlatepkt = 0
    else:
        cmd_dict = CObjectRefStore.Get(OBJ_KEY)
        exp_pktloss = cmd_dict['exp_pktloss']
        exp_avgjitter = cmd_dict['exp_avgjitter']
        exp_maxjitter = cmd_dict['exp_maxjitter']
        exp_avglatency = cmd_dict['exp_avglatency']
        exp_maxlatency = cmd_dict['exp_maxlatency']
        exp_maxoop = cmd_dict['exp_maxoop']
        exp_maxlatepkt = cmd_dict['exp_maxlatepkt']

    res_cmd_list = tag_utils.get_tagged_objects_from_string_names(tagname)
    plLogger.LogDebug("res_cmd_list: " + str(res_cmd_list))

    # String input used for queries
    q_devSelect = "DevInfo.SRC AS 'SRC', DevInfo.DST AS 'DST', " + \
        "DevInfo.SVLAN AS 'S-Vlan', DevInfo.CVLAN AS 'C-Vlan'"
    q_devInfo = "(SELECT Vlan.ParentHnd AS ParentHnd, SRC, DST, SVLAN, CVLAN, SbHnd " + \
        "FROM (SELECT VOne.ParentHnd, VOne.Name, VOne.VlanId AS CVLAN, " + \
        "VTwo.ParentHnd, VTwo.Name, VTwo.VlanId AS SVLAN FROM VlanIf as VOne " + \
        "JOIN VlanIf as VTwo ON VOne.ParentHnd = VTwo.ParentHnd WHERE " + \
        "VOne.Handle != VTwo.Handle GROUP BY VOne.ParentHnd) AS Vlan " + \
        "JOIN (SELECT DstInfo.Address AS DST, SrcInfo.Address AS SRC, " + \
        "SrcInfo.SourceHnd AS SbHnd, SrcInfo.ParentHnd AS ParentHnd FROM " + \
        "(SELECT * FROM IPv4If AS Ip JOIN (SELECT * FROM RelationTable " + \
        "WHERE Type = 'DstBinding') As Dst ON Ip.Handle = Dst.TargetHnd) AS DstInfo " + \
        "JOIN (SELECT * FROM Ipv4If AS Ip JOIN (SELECT * FROM RelationTable " + \
        "WHERE Type = 'SrcBinding') As Src ON Ip.Handle = Src.TargetHnd) " + \
        "AS SrcInfo ON SrcInfo.SourceHnd = DstInfo.SourceHnd) AS Ip ON " + \
        "Ip.ParentHnd = Vlan.ParentHnd GROUP BY SbHnd) As DevInfo"

    for cmd in res_cmd_list:
        if cmd.IsTypeOf(PKG + '.VerifyMultipleDbQueryCommand'):
            q_list = []
            display_name_list = []
            pass_list = []
            fail_list = []

            display_name_list.append("Mean Frame Transfer Delay (FTD) Results")
            pass_list.append("Mean FTD is within the configured threshold of " +
                             str(exp_avglatency) + " ms.")
            fail_list.append("Mean FTD exceeded the configured threshold of " +
                             str(exp_avglatency) + " ms.")
            q = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "ROUND(AvgLatency*1e-3,3) AS 'Mean FTD (ms)', " + \
                str(exp_avglatency) + " AS 'Mean FTD Threshold (ms)' " + \
                "FROM " + str(q_devInfo) + " JOIN RxEotStreamResults As RxStr " + \
                "JOIN StreamBlock AS Sb ON RxStr.ParentStreamBlock == Sb.Handle " + \
                "WHERE DevInfo.SbHnd = Sb.Handle AND " + \
                "ROUND(AvgLatency*1e-3,3) > " + str(exp_avglatency)
            q_list.append(q)

            display_name_list.append("Max Frame Transfer Delay (FTD) Results")
            pass_list.append("Max FTD is within the configured threshold of " +
                             str(exp_maxlatency) + " ms.")
            fail_list.append("Max FTD exceeded the configured threshold of " +
                             str(exp_maxlatency) + " ms.")
            q = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "ROUND(MaxLatency*1e-3,3) AS 'Max FTD (ms)', " + \
                str(exp_maxlatency) + " AS 'Max FTD Threshold (ms)' " + \
                "FROM " + str(q_devInfo) + " JOIN RxEotStreamResults As RxStr " + \
                "JOIN StreamBlock AS Sb ON RxStr.ParentStreamBlock == Sb.Handle " + \
                "WHERE DevInfo.SbHnd = Sb.Handle AND " + \
                "ROUND(MaxLatency*1e-3,3) > " + str(exp_maxlatency)
            q_list.append(q)

            display_name_list.append("RFC4689 Mean Frame Delay Variation (FDV) Results")
            pass_list.append("RFC4689 Mean FDV is within the configured threshold of " +
                             str(exp_avgjitter) + " ms.")
            fail_list.append("RFC4689 Mean FDV exceeded the configured threshold of " +
                             str(exp_avgjitter) + " ms.")
            q = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "ROUND(AvgJitter*1e-3,3) AS 'RFC4689 Mean FDV (ms)', " + \
                str(exp_avgjitter) + " AS 'RFC4689 Mean FDV Threshold (ms)' " + \
                "FROM " + str(q_devInfo) + " JOIN RxEotStreamResults As RxStr " + \
                "JOIN StreamBlock AS Sb ON RxStr.ParentStreamBlock == Sb.Handle " + \
                "WHERE DevInfo.SbHnd = Sb.Handle AND " + \
                "ROUND(AvgJitter*1e-3,3) > " + str(exp_avgjitter)
            q_list.append(q)

            display_name_list.append("Max Frame Delay Variation (FDV) Results")
            pass_list.append("Max FDV is within the configured threshold of " +
                             str(exp_maxjitter) + " ms.")
            fail_list.append("Max FDV exceeded the configured threshold of " +
                             str(exp_maxjitter) + " ms.")
            q = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "ROUND(MaxJitter*1e-3,3) AS 'Max FDV (ms)', " + \
                str(exp_maxjitter) + " AS 'Max FDV Threshold (ms)' " + \
                "FROM " + str(q_devInfo) + " JOIN RxEotStreamResults As RxStr " + \
                "JOIN StreamBlock AS Sb ON RxStr.ParentStreamBlock == Sb.Handle " + \
                "WHERE DevInfo.SbHnd = Sb.Handle AND " + \
                "ROUND(MaxJitter*1e-3,3) > " + str(exp_maxjitter)
            q_list.append(q)

            display_name_list.append("Frame Loss (FL) Results")
            pass_list.append("Frame Loss Count is within the configured threshold of " +
                             str(exp_pktloss) + ".")
            fail_list.append("Frame Loss Count exceeded the configured threshold of " +
                             str(exp_pktloss) + ".")
            q = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "TxRes.FrameCount - RxRes.FrameCount As 'FL Count', " + \
                str(exp_pktloss) + " AS 'FL Count Threshold' " + \
                "FROM " + str(q_devInfo) + " JOIN RxEotStreamResults AS RxRes " + \
                "JOIN TxEotStreamResults AS TxRes JOIN Streamblock AS Sb " + \
                "ON RxRes.ParentStreamBlock = TxRes.ParentStreamblock AND " + \
                "TxRes.ParentStreamblock = Sb.Handle " + \
                "WHERE DevInfo.SbHnd = Sb.Handle AND " + \
                "TxRes.FrameCount - RxRes.FrameCount > " + str(exp_pktloss)
            q_list.append(q)

            display_name_list.append("Out of Order Frame Results")
            pass_list.append("Out of Order Frame Count is within the configured threshold of " +
                             str(exp_maxoop) + ".")
            fail_list.append("Out of Order Frame Count exceeded the configured threshold of " +
                             str(exp_maxoop) + ".")
            q = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "OutSeqFrameCount AS 'Out of Order Frame Count', " + \
                str(exp_maxoop) + " AS 'Out of Order Frame Count Threshold' " + \
                "FROM " + str(q_devInfo) + " JOIN RxEotStreamResults As RxStr " + \
                "JOIN StreamBlock AS Sb ON RxStr.ParentStreamBlock == Sb.Handle " + \
                "WHERE DevInfo.SbHnd = Sb.Handle AND " + \
                "OutSeqFrameCount > " + str(exp_maxoop)
            q_list.append(q)

            display_name_list.append("Late Frame Results")
            pass_list.append("Late Frame Count is within the configured threshold of " +
                             str(exp_maxlatepkt) + ".")
            fail_list.append("Late Frame Count exceeded the configured threshold of " +
                             str(exp_maxlatepkt) + ".")
            q = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "LateFrameCount AS 'Late Frame Count', " + \
                str(exp_maxlatepkt) + " AS 'Late Frame Count Threshold' " + \
                "FROM " + str(q_devInfo) + " JOIN RxEotStreamResults As RxStr " + \
                "JOIN StreamBlock AS Sb ON RxStr.ParentStreamBlock == Sb.Handle " + \
                "WHERE DevInfo.SbHnd = Sb.Handle AND " + \
                "LateFrameCount > " + str(exp_maxlatepkt)
            q_list.append(q)

            cmd.SetCollection('DisplayNameList', display_name_list)
            cmd.SetCollection('PassedVerdictExplanationList', pass_list)
            cmd.SetCollection('FailedVerdictExplanationList', fail_list)
            cmd.SetCollection('SqlQueryList', q_list)
            cmd.Set('UseMultipleResultsDatabases', True)

        elif cmd.IsTypeOf(PKG + '.VerifyDbQueryCommand'):
            query = "SELECT Sb.Name AS 'Streamblock', " + str(q_devSelect) + \
                ", Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
                "Lp.Load || CASE Lp.LoadUnit " + \
                "WHEN 'PERCENT_LINE_RATE' THEN '%' " + \
                "WHEN 'BITS_PER_SECOND' THEN 'bps' " + \
                "WHEN 'KILOBITS_PER_SECOND' THEN 'Kbps' " + \
                "WHEN 'MEGABITS_PER_SECOND' THEN 'Mbps' " + \
                "WHEN 'FRAMES_PER_SECOND' THEN 'Fps' " + \
                "ELSE '' END AS 'CIR', " + \
                "TxRes.FrameCount-RxRes.FrameCount AS 'FL Count', " + \
                "ROUND(CAST(TxRes.FrameCount-RxRes.FrameCount AS " + \
                "FLOAT)/TxRes.FrameCount,3) AS 'FL Ratio', " + \
                "ROUND(MinLatency*1e-3,3) AS 'Min FTD (ms)', " + \
                "ROUND(AvgLatency*1e-3,3) AS 'Mean FTD (ms)', " + \
                "ROUND(MaxLatency*1e-3,3) AS 'Max FTD (ms)', " + \
                "ROUND(MinJitter*1e-3,3) AS 'Min FDV (ms)', " + \
                "ROUND(AvgJitter*1e-3,3) AS 'Mean FDV (ms)', " + \
                "ROUND(MaxJitter*1e-3,3) AS 'Max FDV (ms)', " + \
                "OutSeqFrameCount AS 'Out of Order Frame Count', " + \
                "LateFrameCount AS 'Late Frame Count' " + \
                "FROM " + str(q_devInfo) + \
                " JOIN RxEotStreamResults as RxRes JOIN TxEotStreamResults as TxRes ON " + \
                "TxRes.ParentStreamBlock = RxRes.ParentStreamBlock JOIN Streamblock AS Sb " + \
                "ON TxRes.ParentStreamBlock = Sb.Handle JOIN RelationTable as Rt ON " + \
                "Rt.type = 'AffiliationStreamBlockLoadProfile' AND Sb.Handle = Rt.SourceHnd " + \
                "JOIN StreamBlockLoadProfile as Lp ON Lp.Handle = Rt.TargetHnd " + \
                "WHERE DevInfo.SbHnd = Sb.Handle"

            cmd.Set('SqlQuery', query)
            cmd.Set('DisplayName', 'Y.1564 Summary Results')
            cmd.Set('PassedVerdictExplanation', 'Y.1564 Summary Results')
            cmd.Set('FailedVerdictExplanation', 'ERROR found in Y.1564 KPI Results.')
            cmd.Set('UseMultipleResultsDatabases', True)
            cmd.Set('ApplyVerdictToSummary', False)
            cmd.Set('OperationType', 'GREATER_THAN_OR_EQUAL')
            cmd.Set('RowCount', 0L)
    return ""