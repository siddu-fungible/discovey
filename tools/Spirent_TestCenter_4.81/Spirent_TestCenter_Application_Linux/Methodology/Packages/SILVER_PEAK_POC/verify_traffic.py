from StcIntPythonPL import *
import spirent.methodology.utils.data_operation_utils as data_utils


def run(tagname, b, params):
    logger = PLLogger.GetLogger('methodology')
    logger.LogInfo("Running verify_traffic script")

    # Get PoliciesTxRx table data
    src = {
        "sql_statement": [
            {"static": "SELECT * FROM PoliciesTxRx"}
        ]
    }
    err_str, table_data = data_utils.sql_query(src)
    if err_str:
        return err_str

    # Append a PassFail column
    columns = table_data["row_data"]["column_names"]
    columns.append("PassFail")

    # Go through all the rows/stream blocks
    rows = table_data["row_data"]["rows"]
    for row in rows:
        # Get Rx_FrameCount and ExpectedRx columns
        if row[2] is None:
            # Value may be None type if no traffic received
            rx_frame_count = 0
        else:
            rx_frame_count = int(row[2])
        expected_rx = row[4]

        # A pass is if we're expecting traffic and we got at least one packet
        # or if we're not expecting traffic and received no packets, else fail
        if (expected_rx == "True" and rx_frame_count > 0) or \
           (expected_rx == "False" and rx_frame_count == 0):
            row.append("PASS")
        else:
            row.append("FAIL")

    # Push the table with the new PassFail column back into the DB
    dst = {
        "db_name": "SUMMARY",
        "table_name": "PoliciesTxRxVerdict"
    }
    err_str, verdict = data_utils.send_data_to_db_table(table_data, dst, [])
    if err_str:
        return err_str

    return ""


def verify_http(tagname, b, params):
    # Get table data from HttpResultsWithExpected
    src = {
        "sql_statement": [
            {"static": "SELECT * FROM HttpResultsWithExpected"}
        ]
    }
    err_str, table_data = data_utils.sql_query(src)
    if err_str:
        return err_str

    # Get table rows
    if "row_data" not in table_data:
        return "No HTTP result data found in table HttpResultsWithExpected. " + \
               "Something went wrong getting HTTP results"
    rows = table_data["row_data"]["rows"]
    if len(rows) == 0:
        return "No HTTP result rows found in table HttpResultsWithExpected. " + \
               "Something went wrong getting HTTP results"

    # Append a PassFail column
    columns = table_data["row_data"]["column_names"]
    columns.append("PassFail")

    # For each row determine if its a pass or fail
    for row in rows:
        # attempted = row[1]
        successful = int(row[2])
        # unsuccessful = row[3]
        # aborted = row[4]
        expected_rx = row[5]

        # TODO Can make this If statement better...
        if expected_rx == "False":
            # If we're not expecting, fail if there's at least one successful transaction
            if successful > 0:
                row.append("FAIL")
            else:
                row.append("PASS")
        elif expected_rx == "True":
            # If we are expecting, pass if at least one successful transaction
            if successful > 1:
                row.append("PASS")
            else:
                row.append("FAIL")
        else:
            return "ExpectedRx column in table HttpResultsWithExpected is " + str(expected_rx) + \
                   ". Was expecting either True or False"

    # Push the table with the new PassFail column back into the DB
    dst = {
        "db_name": "SUMMARY",
        "table_name": "HttpResultsVerdict"
    }
    err_str, verdict = data_utils.send_data_to_db_table(table_data, dst, [])
    if err_str:
        return err_str

    return ""
