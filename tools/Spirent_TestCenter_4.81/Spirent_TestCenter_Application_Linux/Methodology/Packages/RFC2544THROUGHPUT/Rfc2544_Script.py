from StcIntPythonPL import *
import json
# import spirent.methodology.utils.json_utils as json_utils
import spirent.methodology.utils.tag_utils as tag_utils


PKG = "spirent.methodology"


# input_dict:
#   EnableLearning: True or Fale boolean
#   LearningMode: L2 or L3 enum
# output_dict:
#   EnableL2Learning: True or False
#   EnableL3Learning: True or False
def Rfc2544ThroughputConfigureLearning(input_dict):
    output_dict = {}
    err_msg = ""

    enable_learning = input_dict["EnableLearning"]
    learning_mode = input_dict["LearningMode"]

    # Both disabled by default
    output_dict["EnableL2Learning"] = "False"
    output_dict["EnableL3Learning"] = "False"

    # If learning enabled, determine which mode is selected
    if enable_learning == "True":
        if learning_mode == "L2":
            output_dict["EnableL2Learning"] = "True"
        elif learning_mode == "L3":
            output_dict["EnableL3Learning"] = "True"

    return output_dict, err_msg


# input_dict: input dictionary from txml with property ids replaced with user input values
# output_dict: dictionary of json data formatted for Create_____MixCommand
def Rfc2544ThroughputMixInfoProcFunction(input_dict):
    plLogger = PLLogger.GetLogger('methodology')
    plLogger.LogDebug('begin Rfc2544ThroughputMixInfoProcFunction')
    plLogger.LogDebug('input_dict: ' + str(input_dict))
    output_dict = {}

    # Direct pass through of input dict to the output dict
    # If the JSON is invalid, the target command will catch it
    output_dict["MixInfo"] = json.dumps(input_dict["input"])

    plLogger.LogDebug('output_dict: ' + str(output_dict))
    plLogger.LogDebug('end Rfc2544ThroughputMixInfoProcFunction')
    return output_dict, ""


def Rfc2544ThroughputSetupCreateTableCmds(tagname, b, params):
    # plLogger = PLLogger.GetLogger('methodology')
    # plLogger.LogDebug("Running Rfc2544ThroughputSetupCreateTableCmds")

    res_cmd_list = tag_utils.get_tagged_objects_from_string_names(tagname)

    objectIterIndex = 0
    rateIterIndex = 0
    createTable1Index = 0
    createTable2Index = 0
    for idx, cmd in enumerate(res_cmd_list):
        if cmd.IsTypeOf(PKG + '.ObjectIteratorCommand'):
            objectIterIndex = idx
        if cmd.IsTypeOf(PKG + '.RateIteratorCommand'):
            rateIterIndex = idx
        if cmd.IsTypeOf(PKG + '.AddRowToDbTableCommand'):
            if createTable1Index == 0:
                createTable1Index = idx
            else:
                createTable2Index = idx

    # Get last frame size and load and determine if the rate iterator converged
    curFrameSize = res_cmd_list[objectIterIndex].Get('CurrVal')
    curLoad = res_cmd_list[rateIterIndex].Get('CurrVal')
    isConverged = res_cmd_list[rateIterIndex].Get('IsConverged')

    # Get converged load or use current load if it didn't converge
    convergedLoad = 0
    if isConverged:
        convergedLoad = res_cmd_list[rateIterIndex].Get('ConvergedVal')
        isConvergedText = "True"
    else:
        convergedLoad = curLoad
        isConvergedText = "False"

    create1 = "CREATE TABLE MethRfc2544Throughput ('FrameSize' INTEGER, 'FPS' FLOAT, " + \
              "'Load' FLOAT, 'MbpsLoad' FLOAT, 'RxLoad' FLOAT, 'RxFPS' FLOAT, " + \
              "'RxCount' INTEGER, 'DroppedCount' INTEGER, " + \
              "'ReorderedCount' INTEGER, 'DuplicateCount' INTEGER, 'TxPort' VARCHAR, " + \
              "'RxPort' VARCHAR, 'IsExpected' TEXT)"
    # For a frame size, get all rows for converged value (or currVal if not converged)
    query1 = "SELECT Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
             "CASE WHEN Sb.FpsLoad < 0 THEN 0.00 " + \
             "ELSE ROUND(Sb.FpsLoad-0.005,2) END AS 'Frames per Second', " + \
             "Sb.PercentageLoad AS 'Load %', " + \
             "Sb.MbpsLoad AS 'Load (Mbps)', " + \
             "((((RxRes.L1BitCount / 1000000.0) / ((RxRes.LastArrivalTime - " + \
             "RxRes.FirstArrivalTime) / 1000000.0)) / ((Sb.MbpsLoad * 100.0) / " + \
             "Sb.PercentageLoad)) * 100.0) AS 'Rx Load (%)', " + \
             "(RxRes.FrameCount / ((RxRes.LastArrivalTime - " + \
             "RxRes.FirstArrivalTime) / 1000000.0)) AS 'Rx Rate (fps)', " + \
             "RxRes.SigFrameCount AS 'Rx Frame Count', " + \
             "RxRes.DroppedFrameCount AS 'Dropped Frame Count', " + \
             "RxRes.ReorderedFrameCount AS 'Reordered Frame Count', " + \
             "RxRes.DuplicateFrameCount AS 'Duplicate Frame Count', " + \
             "(SELECT Port.Location FROM Port WHERE Port.Handle = TxRes.ParentHnd) " + \
             "AS 'Tx Port', " + \
             "(SELECT Port.Location FROM Port WHERE Port.Handle = RxRes.ParentHnd) " + \
             "AS 'Rx Port', " + \
             "(CASE WHEN RxRes.IsExpectedPort=1 THEN 'True' ELSE 'False' END) AS 'Is Expected' " + \
             "From RxEotStreamResults AS RxRes JOIN TxEotStreamResults AS TxRes " + \
             "JOIN Streamblock AS Sb ON RxRes.ParentStreamBlock " + \
             "= TxRes.ParentStreamblock " + \
             "AND TxRes.ParentStreamblock = Sb.Handle WHERE Sb.FixedFrameLength == " + \
             str(curFrameSize) + " AND Sb.PercentageLoad == " + str(convergedLoad)
    res_cmd_list[createTable1Index].Set('SqlCreateTable', create1)
    res_cmd_list[createTable1Index].Set('SqlQuery', query1)

    create2 = "CREATE TABLE MethRfc2544ThroughputFrameRate (" + \
              "'FrameSize' INTEGER, 'FPS' FLOAT, " + \
              "'Load' FLOAT, 'DroppedCount' INTEGER, 'MaxRate' FLOAT, " + \
              "'MaxLoad' FLOAT, 'RxLoad' FLOAT, 'RxFPS' FLOAT, 'LineSpeed' FLOAT, " + \
              "'Converged' TEXT)"
    # For a frame size and converged value (or currVal if not converged), get the row with
    # highest FPS (if multiple ports at different speeds)
    # If there's streams with dropped frames, get the row with the highest dropped count
    # Calculation of max rate from content\traffictests\custom\bll\src\TheoreticalMaxLineRate.cpp
    query2 = "SELECT Sb.FixedFrameLength AS 'Frame Size (bytes)', " + \
             "CASE WHEN Sb.FpsLoad < 0 THEN 0.00 " + \
             "ELSE ROUND(Sb.FpsLoad-0.005,2) END AS 'Frames per Second', " + \
             "Sb.PercentageLoad AS 'Load (%)', " + \
             "RxRes.DroppedFrameCount AS 'Dropped Frame Count', " + \
             "(Sb.FpsLoad * 100.0) / Sb.PercentageLoad AS 'Theoretical Max Rate', " + \
             "100 'Max Load %', " + \
             "(CASE WHEN RxRes.IsExpectedPort=1 THEN ((((RxRes.L1BitCount / 1000000.0) / ((RxRes.LastArrivalTime - " + \
             "RxRes.FirstArrivalTime) / 1000000.0)) / ((Sb.MbpsLoad * 100.0) / " + \
             "Sb.PercentageLoad)) * 100.0) ELSE 0 END) AS 'Rx Load (%)', " + \
             "(CASE WHEN RxRes.IsExpectedPort=1 THEN (RxRes.FrameCount / ((RxRes.LastArrivalTime - " + \
             "RxRes.FirstArrivalTime) / 1000000.0)) ELSE 0 END) AS 'Rx Rate (fps)', " + \
             "((Sb.MbpsLoad * 100.0) / Sb.PercentageLoad) AS 'Line Speed', '" + \
             str(isConvergedText) + "' AS 'Converged' " + \
             "FROM RxEotStreamResults AS RxRes JOIN TxEotStreamResults AS TxRes JOIN " + \
             "Streamblock AS Sb ON " + \
             "RxRes.ParentStreamBlock = TxRes.ParentStreamblock AND " + \
             "TxRes.ParentStreamblock = Sb.Handle " + \
             "WHERE Sb.FixedFrameLength == " + str(curFrameSize) + " AND Sb.PercentageLoad == " + \
             str(convergedLoad) + " ORDER BY RxRes.DroppedFrameCount DESC, Sb.FpsLoad DESC LIMIT 1"
    res_cmd_list[createTable2Index].Set('SqlCreateTable', create2)
    res_cmd_list[createTable2Index].Set('SqlQuery', query2)

    return ""


def Rfc2544ThroughputVerifyResults(tagname, b, params):
    # plLogger = PLLogger.GetLogger('methodology')
    # plLogger.LogDebug("Running Rfc2544ThroughputVerifyResults")

    res_cmd_list = tag_utils.get_tagged_objects_from_string_names(tagname)
    # plLogger.LogDebug("res_cmd_list: " + str(res_cmd_list))

    objectIterIndex = 0
    multiDbQueryIndex = 0
    for idx, cmd in enumerate(res_cmd_list):
        if cmd.IsTypeOf(PKG + '.ObjectIteratorCommand'):
            objectIterIndex = idx
        if cmd.IsTypeOf(PKG + '.VerifyMultipleDbQueryCommand'):
            multiDbQueryIndex = idx

    # Get list of frame sizes from object iterator
    frameList = res_cmd_list[objectIterIndex].GetCollection('ValueList')
    # plLogger.LogDebug("frameList: " + str(frameList))

    q_list = []
    display_name_list = []
    pass_list = []
    fail_list = []
    for frame in frameList:
        # For each frame size determine if there was any streams with dropped frames
        # If so (number of rows found > 0), that is considered a failure
        display_name_list.append('Frame Size ' + str(frame))
        pass_list.append('Found frame rate with no dropped frames for frame size ' + str(frame))
        fail_list.append('Unable to find max frame rate for frame size ' + str(frame))
        q = "SELECT FrameSize AS 'Frame Size (bytes)', Load AS 'Load %', " + \
            "FPS AS 'Frames per Second', RxCount AS 'Rx Frame Count', DroppedCount AS " + \
            "'Dropped Frame Count', RxPort AS 'Rx Port' From MethRfc2544Throughput WHERE " + \
            "FrameSize == " + str(frame) + " AND ((RxCount = 0) OR (DroppedCount > 0)) " + \
            "AND IsExpected = 'True'"
        q_list.append(q)

    res_cmd_list[multiDbQueryIndex].SetCollection('DisplayNameList', display_name_list)
    res_cmd_list[multiDbQueryIndex].SetCollection('PassedVerdictExplanationList', pass_list)
    res_cmd_list[multiDbQueryIndex].SetCollection('FailedVerdictExplanationList', fail_list)
    res_cmd_list[multiDbQueryIndex].SetCollection('SqlQueryList', q_list)
    res_cmd_list[multiDbQueryIndex].Set('UseMultipleResultsDatabases', False)
    res_cmd_list[multiDbQueryIndex].Set('UseSummary', True)

    return ""


def get_procfunction_input_schema():
    return '''
    {
        "type": "object",
        "properties": {
            "id": {
                "type": "string"
            },
            "scriptFile": {
                "type": "string"
            },
            "entryFunction": {
                "type": "string"
            },
            "input": {
                "type": "object"
            },
            "output": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scriptVarName": {
                            "type": "string"
                        },
                        "epKey": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    }
    '''
