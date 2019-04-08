import xlsxwriter
import argparse
import logging
import sys
from lib.utilities.fun_excel import TcmsExcel, TEST_CASES_SHEET_NAME
from lib.utilities.jira_manager import JiraManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(hdlr=handler)
logger.setLevel(logging.DEBUG)

conflicts_seen = False
error_seen = False
def log_to_conflict_file(message, conflict_file):
    global conflicts_seen
    conflicts_seen = True
    with open(conflict_file, "a") as f:
        f.write(message + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UploadTestCases")
    parser.add_argument('--input_file', required=True,
                        dest="input_file",
                        help="Input xlsx file containing the Test-cases")
    parser.add_argument('--output_file',
                        dest="output_file",
                        default="uploaded_results.xlsx",
                        help="Output xlsx file containg the test-cases with JIRA Ids for successful uploads")
    parser.add_argument('--conflict_file',
                        default="conflicts.txt",
                        help="A file containing rows that could not be uploaded to JIRA")
    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    conflict_file = args.conflict_file

    with open(conflict_file, "w") as f:
        pass
    tcms_excel = TcmsExcel(workbook_filename=input_file)
    logger.debug("Validating input xlsx file")
    tcms_excel.validate()
    logger.debug("Input xlsx file is valid")

    workbook = xlsxwriter.Workbook(output_file)
    format = workbook.add_format({'text_wrap': True})
    worksheet = workbook.add_worksheet(name=TEST_CASES_SHEET_NAME)

    jira_manager = JiraManager()
    for row_index in range(0, tcms_excel.get_num_rows()):
        columns = tcms_excel.get_columns_by_row(row_index=row_index)
        create_test_case = False
        if row_index:
            jira_id = tcms_excel.get_value_from_row_by_key(row=columns, key="Jira-Id")

            if jira_id:
                jira_id = int(jira_id)
            if not jira_id:
                logger.debug("We should create a test-case")
                create_test_case = True

            module = tcms_excel.get_value_from_row_by_key(row=columns, key="Module")  # Done
            components = tcms_excel.get_value_from_row_by_key(row=columns, key="Components") # Done
            test_type = tcms_excel.get_value_from_row_by_key(row=columns, key="Test-type") # Done
            test_bed = tcms_excel.get_value_from_row_by_key(row=columns, key="Test-bed") # Done
            summary = tcms_excel.get_value_from_row_by_key(row=columns, key="Summary") # Done
            priority = tcms_excel.get_value_from_row_by_key(row=columns, key="Priority") # Done
            setup = tcms_excel.get_value_from_row_by_key(row=columns, key="Setup") # Done
            description = tcms_excel.get_value_from_row_by_key(row=columns, key="Description") # Done
            expected_result = tcms_excel.get_value_from_row_by_key(row=columns, key="Expected-result")
            variations = tcms_excel.get_value_from_row_by_key(row=columns, key="Variations") # Done
            automatable = tcms_excel.get_value_from_row_by_key(row=columns, key="Automatable") # Done

            if create_test_case:

                components = [x.strip() for x in components.split(",")]
                summary_exists = False
                # Check if a bug with the summary already exists
                existing_id = jira_manager.summary_exists(summary=summary, module=module, components=components)
                if existing_id:
                    exception_message = "Row index: {} Summary: {} already exists in JIRA".format(row_index, summary)
                    log_to_conflict_file(message=exception_message, conflict_file=conflict_file)

                if not existing_id:
                    logger.debug("Creating JIRA for row: {},  {}".format(row_index, summary))
                    new_jira_id = None
                    try:
                        new_jira_id = jira_manager.create_test_case(summary=summary.replace("\n", ""),
                                                                    module=module,
                                                                    components=components,
                                                                    test_type=test_type,
                                                                    priority=priority,
                                                                    expected_result=expected_result,
                                                                    automatable=automatable,
                                                                    test_bed=test_bed,
                                                                    description=description,
                                                                    setup=setup,
                                                                    variations=variations)
                        if not new_jira_id:
                            raise Exception("Unable to create JIRA Id Row: {} Summary: {}".format(row_index, summary))
                    except Exception as ex:
                        exception_message = "Unable to create a test case for Row: {} Summary:{} {}".format(row_index, summary, str(ex))
                        log_to_conflict_file(message=exception_message, conflict_file=conflict_file)
                        logger.critical(exception_message)
                        error_seen = True
                else:
                    new_jira_id = existing_id
            else:
                components = [x.strip() for x in components.split(",")]

                # Let's try to update the test-case
                logger.debug("Updating JIRA for Id: {} {}".format(jira_id, summary))
                jira_manager.update_test_case_with_fields(id=jira_id,
                                                          summary=summary,
                                                          module=module,
                                                          components=components,
                                                          test_type=test_type,
                                                          priority=priority,
                                                          expected_result=expected_result,
                                                          automatable=automatable,
                                                          test_bed=test_bed,
                                                          description=description,
                                                          setup=setup,
                                                          variations=variations)
                logger.debug("Updated")

            # if error_seen:
            #    break
        for column_index, column in enumerate(columns):
            if row_index == 0:
                bold_format = workbook.add_format({'bold': True, 'text_wrap': True})
                worksheet.write(row_index, column_index, column, bold_format)
            else:
                if create_test_case:
                    if column_index == 0 and new_jira_id:
                        worksheet.write(row_index, column_index, new_jira_id, format)
                    else:
                        worksheet.write(row_index, column_index, column, format)
                else:
                    worksheet.write(row_index, column_index, column, format)
    workbook.close()

    if conflicts_seen:
        raise Exception("Conflict detected. Please check {}".format(conflict_file))